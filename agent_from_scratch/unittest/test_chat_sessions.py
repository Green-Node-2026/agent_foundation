import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import fakeredis

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_MODEL", "gpt-test")

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from llm_wrapper import SimpleContent, SimplePart, TokenUsage


def make_fake_session_store():
    """Build a SessionStore backed by fakeredis, bypassing the ping() in __init__."""
    from db import SessionStore
    store = SessionStore.__new__(SessionStore)
    store.client = fakeredis.FakeRedis(decode_responses=True)
    return store


class ChatSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import server

        # Inject fakeredis-backed store; the real one (if any) requires network.
        cls._original_session_store = server.session_store
        server.session_store = make_fake_session_store()

        cls.server = server
        cls.store = server.session_store
        cls.client = TestClient(server.app)

    @classmethod
    def tearDownClass(cls):
        cls.server.session_store = cls._original_session_store

    def setUp(self):
        self.store.client.flushall()
        self.server.usage_tracker._data.clear()

    @staticmethod
    def _fake_run(reply_text: str = "ok", usage: TokenUsage | None = None):
        """Mimic the real agent: the 'done' event's history must include the new user
        message + assistant reply (plus any prior history echoed back), because that's
        what the production loop builds up before yielding."""
        captured = {"history": None, "prompt": None}

        def _hydrate(item):
            return SimpleContent(
                role=item["role"],
                parts=[SimplePart(text=p.get("text")) for p in item.get("parts") or []],
            )

        def runner(prompt, history=None, max_steps=2):
            captured["prompt"] = prompt
            captured["history"] = history

            full = [_hydrate(m) for m in (history or [])]
            full.append(SimpleContent(role="user", parts=[SimplePart(text=prompt)]))
            asst = SimpleContent(role="assistant", parts=[SimplePart(text=reply_text)])
            full.append(asst)

            yield {"type": "model", "content": asst}
            done = {"type": "done", "history": full}
            if usage is not None:
                done["usage"] = usage
            yield done

        runner.captured = captured
        return runner

    # ---------- without X-Session-Id (backward compat) ----------

    def test_chat_without_session_uses_request_history(self):
        runner = self._fake_run()
        request_history = [{"role": "user", "parts": [{"text": "earlier"}]}]

        with patch.object(self.server.agent, "run", side_effect=runner):
            resp = self.client.post(
                "/api/chat",
                json={"prompt": "hello", "history": request_history},
                headers={"X-User-Id": "alice"},
            )

        self.assertEqual(resp.status_code, 200)
        # Stateless path: agent received the body's history verbatim
        self.assertEqual(runner.captured["history"], request_history)
        # No session was touched
        self.assertIsNone(resp.json().get("session_id"))

    # ---------- with X-Session-Id (load from store) ----------

    def test_chat_with_session_loads_history_from_redis(self):
        record = self.store.create("alice", title="t")
        stored_msgs = [{"role": "user", "parts": [{"text": "from_session"}]}]
        self.store.update_messages(record["session_id"], stored_msgs)

        runner = self._fake_run()
        # Body sends a DIFFERENT history that should be ignored when session is set
        body_history = [{"role": "user", "parts": [{"text": "should_be_ignored"}]}]

        with patch.object(self.server.agent, "run", side_effect=runner):
            resp = self.client.post(
                "/api/chat",
                json={"prompt": "next", "history": body_history},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        self.assertEqual(resp.status_code, 200)
        # Agent received session.messages, NOT request.history
        self.assertEqual(runner.captured["history"], stored_msgs)
        self.assertEqual(resp.json()["session_id"], record["session_id"])

    def test_chat_with_session_persists_history(self):
        record = self.store.create("alice")

        runner = self._fake_run(reply_text="response")

        with patch.object(self.server.agent, "run", side_effect=runner):
            self.client.post(
                "/api/chat",
                json={"prompt": "hi"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        saved = self.store.get(record["session_id"])
        # Saved history should contain the assistant turn (system gets filtered out)
        roles = [m["role"] for m in saved["messages"]]
        self.assertIn("assistant", roles)
        self.assertNotIn("system", roles)
        # And updated_at moved forward
        self.assertGreater(saved["updated_at"], record["updated_at"])

    def test_chat_session_messages_accumulate_across_turns(self):
        record = self.store.create("alice")

        # Turn 1
        with patch.object(self.server.agent, "run", side_effect=self._fake_run("turn1")):
            self.client.post(
                "/api/chat",
                json={"prompt": "first"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        after_turn_1 = self.store.get(record["session_id"])["messages"]

        # Turn 2 — agent must receive turn 1's persisted history
        runner_2 = self._fake_run("turn2")
        with patch.object(self.server.agent, "run", side_effect=runner_2):
            self.client.post(
                "/api/chat",
                json={"prompt": "second"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        # Agent.run on turn 2 was called with turn 1's persisted messages
        self.assertEqual(runner_2.captured["history"], after_turn_1)

    # ---------- error paths ----------

    def test_chat_with_unknown_session_returns_404(self):
        resp = self.client.post(
            "/api/chat",
            json={"prompt": "hello"},
            headers={"X-User-Id": "alice", "X-Session-Id": "does_not_exist"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_chat_with_other_users_session_returns_403(self):
        record = self.store.create("alice")
        resp = self.client.post(
            "/api/chat",
            json={"prompt": "hello"},
            headers={"X-User-Id": "bob", "X-Session-Id": record["session_id"]},
        )
        self.assertEqual(resp.status_code, 403)

    def test_chat_without_redis_returns_503_when_session_id_provided(self):
        # Temporarily remove the store to simulate Redis being down at startup
        original = self.server.session_store
        self.server.session_store = None
        try:
            resp = self.client.post(
                "/api/chat",
                json={"prompt": "hello"},
                headers={"X-User-Id": "alice", "X-Session-Id": "anything"},
            )
            self.assertEqual(resp.status_code, 503)
        finally:
            self.server.session_store = original

    # ---------- streaming endpoint ----------

    # ---------- auto-titling ----------

    def test_auto_title_uses_first_user_message(self):
        record = self.store.create("alice", title="")
        runner = self._fake_run()

        with patch.object(self.server.agent, "run", side_effect=runner):
            self.client.post(
                "/api/chat",
                json={"prompt": "What is the meaning of life?"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        saved = self.store.get(record["session_id"])
        self.assertEqual(saved["title"], "What is the meaning of life?")

    def test_auto_title_strips_attached_file_marker(self):
        record = self.store.create("alice", title="")
        runner = self._fake_run()

        with patch.object(self.server.agent, "run", side_effect=runner):
            self.client.post(
                "/api/chat",
                json={"prompt": "Summarize this\n\n[Attached File: report.pdf]"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        saved = self.store.get(record["session_id"])
        self.assertEqual(saved["title"], "Summarize this")

    def test_auto_title_does_not_override_existing(self):
        record = self.store.create("alice", title="My Custom Title")
        runner = self._fake_run()

        with patch.object(self.server.agent, "run", side_effect=runner):
            self.client.post(
                "/api/chat",
                json={"prompt": "anything"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        saved = self.store.get(record["session_id"])
        self.assertEqual(saved["title"], "My Custom Title")

    def test_auto_title_truncates_to_50_chars(self):
        record = self.store.create("alice", title="")
        runner = self._fake_run()
        long_prompt = "a" * 200

        with patch.object(self.server.agent, "run", side_effect=runner):
            self.client.post(
                "/api/chat",
                json={"prompt": long_prompt},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        saved = self.store.get(record["session_id"])
        self.assertEqual(len(saved["title"]), 50)

    def test_stream_with_session_persists_and_echoes_session_id(self):
        record = self.store.create("alice")
        runner = self._fake_run("streamed")

        with patch.object(self.server.agent, "run", side_effect=runner):
            resp = self.client.post(
                "/api/chat/stream",
                json={"prompt": "hi"},
                headers={"X-User-Id": "alice", "X-Session-Id": record["session_id"]},
            )

        self.assertEqual(resp.status_code, 200)

        events = [
            json.loads(line[len("data: "):])
            for line in resp.text.splitlines()
            if line.startswith("data: ")
        ]
        done = next(e for e in events if e["type"] == "done")
        self.assertEqual(done["session_id"], record["session_id"])

        saved = self.store.get(record["session_id"])
        self.assertGreater(len(saved["messages"]), 0)


if __name__ == "__main__":
    unittest.main()

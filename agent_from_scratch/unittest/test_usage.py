import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Set fake env BEFORE importing server. dotenv won't override values already in os.environ,
# so this also wins over a real backend/.env on the developer machine.
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_MODEL", "gpt-test")

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from llm_wrapper import OpenAIProvider, SimpleContent, SimplePart, TokenUsage


class UsageTrackerTests(unittest.TestCase):
    def setUp(self):
        from server import UsageTracker
        self.tracker = UsageTracker()

    def test_record_accumulates_tokens(self):
        self.tracker.record("alice", TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15))
        self.tracker.record("alice", TokenUsage(prompt_tokens=20, completion_tokens=8, total_tokens=28))
        today = self.tracker.today("alice")
        self.assertEqual(today["prompt_tokens"], 30)
        self.assertEqual(today["completion_tokens"], 13)
        self.assertEqual(today["total_tokens"], 43)
        self.assertEqual(today["requests"], 2)

    def test_record_none_is_noop(self):
        self.tracker.record("alice", None)
        today = self.tracker.today("alice")
        self.assertEqual(today["prompt_tokens"], 0)
        self.assertEqual(today["completion_tokens"], 0)
        self.assertEqual(today["requests"], 0)

    def test_today_for_unseen_user_returns_zero(self):
        today = self.tracker.today("ghost")
        self.assertEqual(today["prompt_tokens"], 0)
        self.assertEqual(today["completion_tokens"], 0)
        self.assertEqual(today["total_tokens"], 0)
        self.assertEqual(today["requests"], 0)
        self.assertEqual(today["user_id"], "ghost")

    def test_users_are_isolated(self):
        self.tracker.record("alice", TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15))
        self.tracker.record("bob", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))
        self.assertEqual(self.tracker.today("alice")["total_tokens"], 15)
        self.assertEqual(self.tracker.today("bob")["total_tokens"], 150)

    def test_today_includes_iso_date(self):
        self.assertEqual(self.tracker.today("alice")["date"], date.today().isoformat())


class OpenAIProviderUsageTests(unittest.TestCase):
    def setUp(self):
        # Bypass __init__ so we don't hit OpenAI() construction.
        self.provider = OpenAIProvider.__new__(OpenAIProvider)
        self.provider.client = MagicMock()
        self.provider.model = "test-model"

    def _stub_response(self, usage_obj):
        message = SimpleNamespace(content="hello", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage_obj)

    def test_usage_extracted_when_present(self):
        usage = SimpleNamespace(prompt_tokens=42, completion_tokens=13, total_tokens=55)
        self.provider.client.chat.completions.create.return_value = self._stub_response(usage)

        result = self.provider.generate(contents=[], tool_definitions=[])

        self.assertIsInstance(result.usage, TokenUsage)
        self.assertEqual(result.usage.prompt_tokens, 42)
        self.assertEqual(result.usage.completion_tokens, 13)
        self.assertEqual(result.usage.total_tokens, 55)

    def test_usage_is_none_when_missing(self):
        self.provider.client.chat.completions.create.return_value = self._stub_response(usage_obj=None)
        result = self.provider.generate(contents=[], tool_definitions=[])
        self.assertIsNone(result.usage)

    def test_partial_usage_fields_default_to_zero(self):
        # Some OpenAI-compatible proxies omit fields. The extractor must not crash.
        usage = SimpleNamespace(prompt_tokens=10)
        self.provider.client.chat.completions.create.return_value = self._stub_response(usage)

        result = self.provider.generate(contents=[], tool_definitions=[])

        self.assertEqual(result.usage.prompt_tokens, 10)
        self.assertEqual(result.usage.completion_tokens, 0)
        self.assertEqual(result.usage.total_tokens, 0)


class UsageEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import server

        cls.server = server
        cls.client = TestClient(server.app)

    def setUp(self):
        self.server.usage_tracker._data.clear()

    def _fake_run(self, usage: TokenUsage | None):
        def runner(prompt, history=None, max_steps=2):
            content = SimpleContent(role="assistant", parts=[SimplePart(text="hi")])
            yield {"type": "model", "content": content}
            done = {"type": "done", "history": [content]}
            if usage is not None:
                done["usage"] = usage
            yield done
        return runner

    def _fake_multi_step_run(self, per_step_usage: list[TokenUsage]):
        """Simulates a ReAct loop with multiple model calls, summing usage on 'done'."""
        def runner(prompt, history=None, max_steps=5):
            content = SimpleContent(role="assistant", parts=[SimplePart(text="step")])
            total = TokenUsage()
            for u in per_step_usage:
                yield {"type": "model", "content": content}
                total.prompt_tokens += u.prompt_tokens
                total.completion_tokens += u.completion_tokens
                total.total_tokens += u.total_tokens
            yield {"type": "done", "history": [content], "usage": total}
        return runner

    def test_get_usage_defaults_to_anonymous(self):
        resp = self.client.get("/api/usage")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["user_id"], "anonymous")
        self.assertEqual(body["total_tokens"], 0)

    def test_get_usage_uses_x_user_id_header(self):
        resp = self.client.get("/api/usage", headers={"X-User-Id": "alice"})
        self.assertEqual(resp.json()["user_id"], "alice")

    def test_chat_endpoint_records_usage(self):
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        with patch.object(self.server.agent, "run", side_effect=self._fake_run(usage)):
            resp = self.client.post(
                "/api/chat",
                json={"prompt": "hello"},
                headers={"X-User-Id": "alice"},
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        # Per-turn footer
        self.assertEqual(body["usage"]["prompt_tokens"], 10)
        self.assertEqual(body["usage"]["completion_tokens"], 5)
        self.assertEqual(body["usage"]["total_tokens"], 15)

        # Running daily total
        daily = body["daily_usage"]
        self.assertEqual(daily["prompt_tokens"], 10)
        self.assertEqual(daily["completion_tokens"], 5)
        self.assertEqual(daily["total_tokens"], 15)
        self.assertEqual(daily["requests"], 1)

    def test_multi_step_turn_aggregates_usage_in_footer(self):
        """ReAct loop with 3 LLM calls should produce one summed footer, not three."""
        steps = [
            TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
            TokenUsage(prompt_tokens=150, completion_tokens=30, total_tokens=180),
            TokenUsage(prompt_tokens=200, completion_tokens=40, total_tokens=240),
        ]
        with patch.object(self.server.agent, "run", side_effect=self._fake_multi_step_run(steps)):
            resp = self.client.post(
                "/api/chat",
                json={"prompt": "weather x 3"},
                headers={"X-User-Id": "alice"},
            )

        body = resp.json()
        self.assertEqual(body["usage"]["prompt_tokens"], 450)
        self.assertEqual(body["usage"]["completion_tokens"], 90)
        self.assertEqual(body["usage"]["total_tokens"], 540)

        # And exactly one "request" (one user turn) recorded daily, not three
        self.assertEqual(body["daily_usage"]["requests"], 1)
        self.assertEqual(body["daily_usage"]["total_tokens"], 540)

    def test_chat_stream_records_usage(self):
        usage = TokenUsage(prompt_tokens=7, completion_tokens=3, total_tokens=10)
        with patch.object(self.server.agent, "run", side_effect=self._fake_run(usage)):
            resp = self.client.post(
                "/api/chat/stream",
                json={"prompt": "hello"},
                headers={"X-User-Id": "bob"},
            )

        self.assertEqual(resp.status_code, 200)
        recorded = self.server.usage_tracker.today("bob")
        self.assertEqual(recorded["prompt_tokens"], 7)
        self.assertEqual(recorded["completion_tokens"], 3)
        self.assertEqual(recorded["requests"], 1)

    def test_users_isolated_across_api_calls(self):
        with patch.object(self.server.agent, "run", side_effect=self._fake_run(
            TokenUsage(prompt_tokens=10, completion_tokens=0, total_tokens=10)
        )):
            self.client.post("/api/chat", json={"prompt": "x"}, headers={"X-User-Id": "alice"})

        with patch.object(self.server.agent, "run", side_effect=self._fake_run(
            TokenUsage(prompt_tokens=50, completion_tokens=0, total_tokens=50)
        )):
            self.client.post("/api/chat", json={"prompt": "x"}, headers={"X-User-Id": "bob"})

        alice = self.client.get("/api/usage", headers={"X-User-Id": "alice"}).json()
        bob = self.client.get("/api/usage", headers={"X-User-Id": "bob"}).json()

        self.assertEqual(alice["prompt_tokens"], 10)
        self.assertEqual(bob["prompt_tokens"], 50)

    def test_chat_with_no_usage_does_not_record(self):
        with patch.object(self.server.agent, "run", side_effect=self._fake_run(usage=None)):
            self.client.post(
                "/api/chat",
                json={"prompt": "hello"},
                headers={"X-User-Id": "ghost"},
            )

        recorded = self.server.usage_tracker.today("ghost")
        self.assertEqual(recorded["requests"], 0)
        self.assertEqual(recorded["total_tokens"], 0)

    def test_stream_emits_usage_only_in_done_event(self):
        usage = TokenUsage(prompt_tokens=11, completion_tokens=4, total_tokens=15)
        with patch.object(self.server.agent, "run", side_effect=self._fake_run(usage)):
            resp = self.client.post(
                "/api/chat/stream",
                json={"prompt": "hello"},
                headers={"X-User-Id": "alice"},
            )

        events = [
            json.loads(line[len("data: "):])
            for line in resp.text.splitlines()
            if line.startswith("data: ")
        ]
        model_events = [e for e in events if e["type"] == "model"]
        done_events = [e for e in events if e["type"] == "done"]

        # Streaming preserved: model event still fires, but without usage
        self.assertEqual(len(model_events), 1)
        self.assertNotIn("usage", model_events[0])

        # Footer carries per-turn usage; daily rollup is fetched separately via /api/usage
        self.assertEqual(len(done_events), 1)
        self.assertEqual(done_events[0]["usage"]["total_tokens"], 15)
        self.assertNotIn("daily_usage", done_events[0])

        # Verify the tracker was still updated server-side
        recorded = self.server.usage_tracker.today("alice")
        self.assertEqual(recorded["total_tokens"], 15)


if __name__ == "__main__":
    unittest.main()

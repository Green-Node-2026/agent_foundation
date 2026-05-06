import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import fakeredis

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db import SESSION_TTL_SECONDS, SessionNotFound, SessionStore


def make_store() -> SessionStore:
    """Build a SessionStore backed by fakeredis, bypassing __init__'s ping()."""
    store = SessionStore.__new__(SessionStore)
    store.client = fakeredis.FakeRedis(decode_responses=True)
    return store


class SessionStoreCreateTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def test_create_returns_record_with_unique_id(self):
        a = self.store.create("alice", title="first")
        b = self.store.create("alice", title="second")
        self.assertNotEqual(a["session_id"], b["session_id"])
        self.assertEqual(a["user_id"], "alice")
        self.assertEqual(a["title"], "first")
        self.assertEqual(a["messages"], [])
        self.assertIn("created_at", a)
        self.assertIn("updated_at", a)

    def test_create_stores_record_under_session_key(self):
        record = self.store.create("alice", title="x")
        raw = self.store.client.get(f"session:{record['session_id']}")
        self.assertIsNotNone(raw)
        self.assertEqual(json.loads(raw), record)

    def test_create_sets_ttl(self):
        record = self.store.create("alice")
        ttl = self.store.client.ttl(f"session:{record['session_id']}")
        # TTL should be close to the configured value (allow small drift)
        self.assertGreater(ttl, SESSION_TTL_SECONDS - 5)
        self.assertLessEqual(ttl, SESSION_TTL_SECONDS)

    def test_create_indexes_in_user_zset(self):
        record = self.store.create("alice")
        members = self.store.client.zrange("user_sessions:alice", 0, -1, withscores=True)
        self.assertEqual(len(members), 1)
        sid, score = members[0]
        self.assertEqual(sid, record["session_id"])
        self.assertAlmostEqual(score, record["updated_at"], places=3)


class SessionStoreGetTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def test_get_returns_full_record(self):
        created = self.store.create("alice", title="hello")
        fetched = self.store.get(created["session_id"])
        self.assertEqual(fetched, created)

    def test_get_raises_when_missing(self):
        with self.assertRaises(SessionNotFound):
            self.store.get("nonexistent")


class SessionStoreUpdateTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def test_update_replaces_messages_and_bumps_updated_at(self):
        created = self.store.create("alice")
        time.sleep(0.01)  # ensure updated_at moves forward

        new_msgs = [{"role": "user", "parts": [{"text": "hi"}]}]
        updated = self.store.update_messages(created["session_id"], new_msgs)

        self.assertEqual(updated["messages"], new_msgs)
        self.assertGreater(updated["updated_at"], created["updated_at"])
        self.assertEqual(updated["created_at"], created["created_at"])
        # title preserved when not passed
        self.assertEqual(updated["title"], created["title"])

    def test_update_can_change_title(self):
        created = self.store.create("alice", title="old")
        updated = self.store.update_messages(created["session_id"], [], title="new")
        self.assertEqual(updated["title"], "new")

    def test_update_refreshes_user_index_score(self):
        created = self.store.create("alice")
        old_score = self.store.client.zscore("user_sessions:alice", created["session_id"])
        time.sleep(0.01)

        self.store.update_messages(created["session_id"], [{"x": 1}])
        new_score = self.store.client.zscore("user_sessions:alice", created["session_id"])
        self.assertGreater(new_score, old_score)

    def test_update_raises_when_missing(self):
        with self.assertRaises(SessionNotFound):
            self.store.update_messages("nonexistent", [])


class SessionStoreListTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def test_list_empty_user_returns_empty(self):
        self.assertEqual(self.store.list_for_user("ghost"), [])

    def test_list_returns_summary_not_full_messages(self):
        created = self.store.create("alice", title="t")
        self.store.update_messages(created["session_id"], [{"a": 1}, {"b": 2}, {"c": 3}])

        sessions = self.store.list_for_user("alice")
        self.assertEqual(len(sessions), 1)
        summary = sessions[0]

        self.assertIn("session_id", summary)
        self.assertIn("title", summary)
        self.assertIn("created_at", summary)
        self.assertIn("updated_at", summary)
        self.assertEqual(summary["message_count"], 3)
        self.assertNotIn("messages", summary)  # keep payload light

    def test_list_sorted_newest_first(self):
        s1 = self.store.create("alice", title="oldest")
        time.sleep(0.01)
        s2 = self.store.create("alice", title="middle")
        time.sleep(0.01)
        s3 = self.store.create("alice", title="newest")

        sessions = self.store.list_for_user("alice")
        ids = [s["session_id"] for s in sessions]
        self.assertEqual(ids, [s3["session_id"], s2["session_id"], s1["session_id"]])

    def test_list_isolates_users(self):
        self.store.create("alice")
        self.store.create("bob")
        self.store.create("bob")

        self.assertEqual(len(self.store.list_for_user("alice")), 1)
        self.assertEqual(len(self.store.list_for_user("bob")), 2)

    def test_list_respects_limit(self):
        for i in range(5):
            self.store.create("alice", title=str(i))
            time.sleep(0.001)

        self.assertEqual(len(self.store.list_for_user("alice", limit=2)), 2)
        self.assertEqual(len(self.store.list_for_user("alice", limit=100)), 5)

    def test_list_cleans_up_stale_index_entries(self):
        """If a session blob expired (TTL) but index still references it, list() should
        prune the stale ZSET entry instead of returning a half-broken record."""
        created = self.store.create("alice", title="will expire")
        # Simulate the session blob expiring: delete the key directly,
        # leaving the user_sessions ZSET entry orphaned.
        self.store.client.delete(f"session:{created['session_id']}")

        # Index still has the orphan
        self.assertEqual(self.store.client.zcard("user_sessions:alice"), 1)

        sessions = self.store.list_for_user("alice")

        # list returns nothing because the only entry was stale
        self.assertEqual(sessions, [])
        # And the orphan was cleaned up from the index
        self.assertEqual(self.store.client.zcard("user_sessions:alice"), 0)


class SessionStoreDeleteTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def test_delete_removes_blob_and_index(self):
        created = self.store.create("alice")
        sid = created["session_id"]

        self.store.delete(sid)

        self.assertIsNone(self.store.client.get(f"session:{sid}"))
        self.assertEqual(self.store.client.zcard("user_sessions:alice"), 0)
        with self.assertRaises(SessionNotFound):
            self.store.get(sid)

    def test_delete_raises_when_missing(self):
        with self.assertRaises(SessionNotFound):
            self.store.delete("nonexistent")

    def test_delete_does_not_affect_other_sessions(self):
        a = self.store.create("alice", title="keep")
        b = self.store.create("alice", title="drop")

        self.store.delete(b["session_id"])

        remaining = self.store.list_for_user("alice")
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["session_id"], a["session_id"])


class SessionStoreHealthTests(unittest.TestCase):
    def test_health_check_true_when_redis_responds(self):
        store = make_store()
        self.assertTrue(store.health_check())

    def test_health_check_false_on_redis_error(self):
        store = make_store()
        # Force any Redis call to raise
        import redis as redis_pkg
        store.client = MagicMock()
        store.client.ping.side_effect = redis_pkg.exceptions.ConnectionError("boom")
        self.assertFalse(store.health_check())


class SessionStoreInitTests(unittest.TestCase):
    def test_init_raises_when_url_missing(self):
        # Ensure no env var leaks in
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("REDIS_URL", None)
            with self.assertRaisesRegex(ValueError, "REDIS_URL not set"):
                SessionStore()


if __name__ == "__main__":
    unittest.main()

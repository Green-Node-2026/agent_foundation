"""Redis-backed chat session storage.

Schema:
    session:{session_id}    → JSON {session_id, user_id, created_at, updated_at, title, messages}
    user_sessions:{user_id} → ZSET (member: session_id, score: updated_at)
"""
import json
import os
import time
import uuid

import redis


SESSION_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days


class SessionNotFound(Exception):
    pass


class SessionStore:
    def __init__(self, url: str | None = None):
        url = url or os.getenv("REDIS_URL")
        if not url:
            raise ValueError("REDIS_URL not set")
        self.client = redis.Redis.from_url(url, decode_responses=True, socket_timeout=5)
        # Fail fast if credentials are wrong — caller decides whether to continue without sessions.
        self.client.ping()

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"session:{session_id}"

    @staticmethod
    def _user_index_key(user_id: str) -> str:
        return f"user_sessions:{user_id}"

    def create(self, user_id: str, title: str = "") -> dict:
        session_id = uuid.uuid4().hex
        now = time.time()
        record = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "title": title,
            "messages": [],
        }
        with self.client.pipeline() as pipe:
            pipe.set(self._session_key(session_id), json.dumps(record), ex=SESSION_TTL_SECONDS)
            pipe.zadd(self._user_index_key(user_id), {session_id: now})
            pipe.execute()
        return record

    def get(self, session_id: str) -> dict:
        raw = self.client.get(self._session_key(session_id))
        if raw is None:
            raise SessionNotFound(session_id)
        return json.loads(raw)

    def update_messages(
        self, session_id: str, messages: list[dict], title: str | None = None
    ) -> dict:
        record = self.get(session_id)
        record["messages"] = messages
        record["updated_at"] = time.time()
        if title is not None:
            record["title"] = title
        with self.client.pipeline() as pipe:
            pipe.set(
                self._session_key(session_id),
                json.dumps(record),
                ex=SESSION_TTL_SECONDS,
            )
            pipe.zadd(
                self._user_index_key(record["user_id"]),
                {session_id: record["updated_at"]},
            )
            pipe.execute()
        return record

    def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        session_ids = self.client.zrevrange(self._user_index_key(user_id), 0, limit - 1)
        if not session_ids:
            return []

        keys = [self._session_key(sid) for sid in session_ids]
        raws = self.client.mget(keys)

        summaries = []
        stale = []
        for sid, raw in zip(session_ids, raws):
            if raw is None:
                # Session expired (TTL) but index still has it — clean up.
                stale.append(sid)
                continue
            data = json.loads(raw)
            summaries.append({
                "session_id": data["session_id"],
                "title": data.get("title", ""),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "message_count": len(data.get("messages", [])),
            })

        if stale:
            self.client.zrem(self._user_index_key(user_id), *stale)

        return summaries

    def delete(self, session_id: str) -> None:
        record = self.get(session_id)  # raises if missing
        with self.client.pipeline() as pipe:
            pipe.delete(self._session_key(session_id))
            pipe.zrem(self._user_index_key(record["user_id"]), session_id)
            pipe.execute()

    def health_check(self) -> bool:
        try:
            return bool(self.client.ping())
        except redis.exceptions.RedisError:
            return False

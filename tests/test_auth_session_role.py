import asyncio
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.routers.auth import get_session


class _FakeScalars:
    def __init__(self, items):
        self._items = list(items)

    def first(self):
        return self._items[0] if self._items else None


class _FakeExecuteResult:
    def __init__(self, scalars=None):
        self._scalars = list(scalars or [])

    def scalars(self):
        return _FakeScalars(self._scalars)


class _FakeAsyncSession:
    def __init__(self, execute_results=None):
        self._execute_results = list(execute_results or [])
        self.commits = 0

    async def execute(self, _stmt):
        if not self._execute_results:
            return _FakeExecuteResult()
        return self._execute_results.pop(0)

    async def commit(self):
        self.commits += 1


class AuthSessionRoleTests(unittest.TestCase):
    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_get_session_includes_role(self):
        now = datetime.now(timezone.utc)
        session_token = "session-token"

        fake_session_row = SimpleNamespace(
            user_id=uuid.uuid4(),
            last_active_at=now,
            expires_at=now + timedelta(hours=1),
        )
        fake_user = SimpleNamespace(
            id=fake_session_row.user_id,
            display_name="Mod Kullanici",
            username="moduser",
            email="mod@example.com",
            role="moderator",
            is_active=True,
            deleted_at=None,
        )

        fake_db = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_session_row]),
                _FakeExecuteResult(scalars=[fake_user]),
            ]
        )
        fake_request = SimpleNamespace(cookies={"session_token": session_token})

        payload = self._run(get_session(fake_request, fake_db))

        self.assertIn("user", payload)
        self.assertEqual(payload["user"]["email"], "mod@example.com")
        self.assertEqual(payload["user"]["role"], "moderator")
        self.assertFalse(payload["user"]["is_admin"])


if __name__ == "__main__":
    unittest.main()

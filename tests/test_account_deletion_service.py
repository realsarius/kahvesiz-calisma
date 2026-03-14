import asyncio
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import HTTPException

from app.services import account_deletion_service


class _FakeScalars:
    def __init__(self, items):
        self._items = list(items)

    def first(self):
        return self._items[0] if self._items else None


class _FakeExecuteResult:
    def __init__(self, scalars=None, rowcount=0):
        self._scalars = list(scalars or [])
        self.rowcount = rowcount

    def scalars(self):
        return _FakeScalars(self._scalars)


class _FakeAsyncSession:
    def __init__(self, execute_results=None):
        self._execute_results = list(execute_results or [])
        self.commits = 0
        self.rollbacks = 0
        self.executed_statements = []

    async def execute(self, _stmt):
        self.executed_statements.append(_stmt)
        if not self._execute_results:
            return _FakeExecuteResult()
        item = self._execute_results.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class AccountDeletionServiceTests(unittest.TestCase):
    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_get_active_user_or_404_returns_user(self):
        user_id = uuid.uuid4()
        fake_user = SimpleNamespace(id=user_id, is_active=True, deleted_at=None)
        fake_db = _FakeAsyncSession(execute_results=[_FakeExecuteResult(scalars=[fake_user])])

        result = self._run(account_deletion_service.get_active_user_or_404(user_id, fake_db))

        self.assertEqual(result.id, user_id)

    def test_get_active_user_or_404_raises_404_for_missing_user(self):
        fake_db = _FakeAsyncSession(execute_results=[_FakeExecuteResult(scalars=[])])

        with self.assertRaises(HTTPException) as exc:
            self._run(account_deletion_service.get_active_user_or_404(uuid.uuid4(), fake_db))

        self.assertEqual(exc.exception.status_code, 404)

    def test_delete_user_account_self_soft_deletes_and_purges(self):
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        target_user = SimpleNamespace(
            id=user_id,
            role="user",
            is_active=True,
            deleted_at=None,
            email_verified_at=now,
        )

        fake_db = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(rowcount=1),
                _FakeExecuteResult(rowcount=4),
                _FakeExecuteResult(rowcount=2),
                _FakeExecuteResult(rowcount=3),
            ]
        )

        summary = self._run(
            account_deletion_service.delete_user_account(
                actor_user=target_user,
                target_user=target_user,
                db=fake_db,
            )
        )

        self.assertFalse(target_user.is_active)
        self.assertIsNotNone(target_user.deleted_at)
        self.assertEqual(fake_db.commits, 1)
        self.assertEqual(summary["mode"], "self")
        self.assertEqual(summary["pii_deleted"], 1)
        self.assertEqual(summary["reviews_anonymized"], 4)
        self.assertEqual(summary["sessions_invalidated"], 2)
        self.assertEqual(summary["tokens_revoked"], 3)
        review_anonymize_stmt = fake_db.executed_statements[1]
        review_params = review_anonymize_stmt.compile().params
        self.assertIn("user_id", review_params)
        self.assertIsNone(review_params["user_id"])

    def test_delete_user_account_forbidden_for_non_admin_targeting_other_user(self):
        actor_user = SimpleNamespace(id=uuid.uuid4(), role="user")
        target_user = SimpleNamespace(id=uuid.uuid4(), role="user", is_active=True, deleted_at=None)
        fake_db = _FakeAsyncSession()

        with self.assertRaises(HTTPException) as exc:
            self._run(
                account_deletion_service.delete_user_account(
                    actor_user=actor_user,
                    target_user=target_user,
                    db=fake_db,
                )
            )

        self.assertEqual(exc.exception.status_code, 403)

    def test_delete_user_account_admin_can_delete_other_user(self):
        actor_user = SimpleNamespace(id=uuid.uuid4(), role="admin")
        target_user = SimpleNamespace(id=uuid.uuid4(), role="user", is_active=True, deleted_at=None)

        fake_db = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(rowcount=1),
                _FakeExecuteResult(rowcount=6),
                _FakeExecuteResult(rowcount=3),
                _FakeExecuteResult(rowcount=4),
            ]
        )

        summary = self._run(
            account_deletion_service.delete_user_account(
                actor_user=actor_user,
                target_user=target_user,
                db=fake_db,
            )
        )

        self.assertEqual(summary["mode"], "admin")
        self.assertTrue(summary["user_soft_deleted"])
        self.assertEqual(fake_db.commits, 1)

    def test_delete_user_account_rolls_back_when_execute_fails(self):
        actor_user = SimpleNamespace(id=uuid.uuid4(), role="admin")
        target_user = SimpleNamespace(id=uuid.uuid4(), role="user", is_active=True, deleted_at=None)

        fake_db = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(rowcount=1),
                RuntimeError("review anonymize failed"),
            ]
        )

        with self.assertRaises(RuntimeError):
            self._run(
                account_deletion_service.delete_user_account(
                    actor_user=actor_user,
                    target_user=target_user,
                    db=fake_db,
                )
            )

        self.assertEqual(fake_db.commits, 0)
        self.assertEqual(fake_db.rollbacks, 1)
        self.assertTrue(target_user.is_active)
        self.assertIsNone(target_user.deleted_at)


if __name__ == "__main__":
    unittest.main()

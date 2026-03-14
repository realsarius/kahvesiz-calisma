import asyncio
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Response

from app.routers import users


class UsersRouterContractTests(unittest.TestCase):
    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_delete_my_account_calls_service_and_clears_cookie(self):
        fake_db = object()
        fake_user = SimpleNamespace(id=uuid.uuid4(), role="user")
        fake_request = SimpleNamespace(headers={}, cookies={})

        with patch.object(users.review_service, "get_current_user", new=AsyncMock(return_value=fake_user)) as get_user_mock, patch.object(
            users.account_deletion_service,
            "delete_user_account",
            new=AsyncMock(return_value={"mode": "self"}),
        ) as delete_service_mock:
            response = self._run(users.delete_my_account(request=fake_request, db=fake_db))

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 204)
        self.assertIn("set-cookie", {k.lower() for k in response.headers.keys()})
        get_user_mock.assert_awaited_once_with(fake_request, fake_db, required=True)
        delete_service_mock.assert_awaited_once_with(
            actor_user=fake_user,
            target_user=fake_user,
            db=fake_db,
        )

    def test_delete_user_as_admin_rejects_non_admin(self):
        fake_db = object()
        fake_request = SimpleNamespace(headers={}, cookies={})
        non_admin_user = SimpleNamespace(id=uuid.uuid4(), role="user")

        with patch.object(users.review_service, "get_current_user", new=AsyncMock(return_value=non_admin_user)):
            with self.assertRaises(HTTPException) as exc:
                self._run(
                    users.delete_user_as_admin(
                        user_id=uuid.uuid4(),
                        request=fake_request,
                        db=fake_db,
                    )
                )

        self.assertEqual(exc.exception.status_code, 403)

    def test_delete_user_as_admin_calls_shared_service(self):
        fake_db = object()
        fake_request = SimpleNamespace(headers={}, cookies={})
        admin_user = SimpleNamespace(id=uuid.uuid4(), role="admin")
        target_user = SimpleNamespace(id=uuid.uuid4(), role="user")

        with patch.object(users.review_service, "get_current_user", new=AsyncMock(return_value=admin_user)) as get_user_mock, patch.object(
            users.account_deletion_service,
            "get_active_user_or_404",
            new=AsyncMock(return_value=target_user),
        ) as get_target_mock, patch.object(
            users.account_deletion_service,
            "delete_user_account",
            new=AsyncMock(return_value={"mode": "admin"}),
        ) as delete_service_mock:
            response = self._run(
                users.delete_user_as_admin(
                    user_id=target_user.id,
                    request=fake_request,
                    db=fake_db,
                )
            )

        self.assertEqual(response.status_code, 204)
        get_user_mock.assert_awaited_once_with(fake_request, fake_db, required=True)
        get_target_mock.assert_awaited_once_with(target_user.id, fake_db)
        delete_service_mock.assert_awaited_once_with(
            actor_user=admin_user,
            target_user=target_user,
            db=fake_db,
        )


if __name__ == "__main__":
    unittest.main()

import asyncio
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import HTTPException

from app.services import review_service
from app.schemas.review import ReviewCreate, VoteCreate


class _FakeScalars:
    def __init__(self, items):
        self._items = list(items)

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)


class _FakeExecuteResult:
    def __init__(self, rows=None, scalars=None):
        self._rows = list(rows or [])
        self._scalars = list(scalars or [])

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return _FakeScalars(self._scalars)

    def scalar_one(self):
        if self._scalars:
            return self._scalars[0]
        if self._rows:
            return self._rows[0]
        return 0


class _FakeAsyncSession:
    def __init__(self, execute_results=None):
        self._execute_results = list(execute_results or [])
        self.added = []
        self.deleted = []
        self.commits = 0

    async def execute(self, _stmt):
        if not self._execute_results:
            return _FakeExecuteResult()
        return self._execute_results.pop(0)

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid.uuid4())
        if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
            setattr(obj, "created_at", datetime.now(timezone.utc))
        if hasattr(obj, "updated_at") and getattr(obj, "updated_at", None) is None:
            setattr(obj, "updated_at", datetime.now(timezone.utc))
        if hasattr(obj, "is_verified_visit") and getattr(obj, "is_verified_visit", None) is None:
            setattr(obj, "is_verified_visit", False)
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        return None

    async def delete(self, obj):
        self.deleted.append(obj)


class ReviewServiceTests(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    def test_create_review_success(self):
        cafe_id = uuid.uuid4()
        user_id = uuid.uuid4()
        fake_user = SimpleNamespace(
            id=user_id,
            username="deneme",
            display_name="Deneme Kullanıcı",
            role="user",
        )
        fake_cafe = SimpleNamespace(id=cafe_id, is_active=True, deleted_at=None)
        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_cafe]),
                _FakeExecuteResult(scalars=[]),
            ]
        )

        payload = ReviewCreate(rating=5, title="Harika", body="Çok memnun kaldım")
        response = self._run(review_service.create_review(cafe_id, payload, fake_user, fake_session))

        self.assertEqual(response.cafe_id, cafe_id)
        self.assertEqual(response.user_id, user_id)
        self.assertEqual(response.rating, 5)
        self.assertEqual(response.reviewer_name, "Deneme Kullanıcı")
        self.assertEqual(fake_session.commits, 1)
        self.assertEqual(len(fake_session.added), 1)

    def test_create_review_duplicate_raises_409(self):
        cafe_id = uuid.uuid4()
        user_id = uuid.uuid4()
        fake_user = SimpleNamespace(id=user_id, username="user", display_name=None, role="user")
        fake_cafe = SimpleNamespace(id=cafe_id, is_active=True, deleted_at=None)
        existing_review = SimpleNamespace(id=uuid.uuid4(), user_id=user_id, cafe_id=cafe_id, deleted_at=None)

        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_cafe]),
                _FakeExecuteResult(scalars=[existing_review]),
            ]
        )

        with self.assertRaises(HTTPException) as exc:
            self._run(
                review_service.create_review(
                    cafe_id,
                    ReviewCreate(rating=4, title="İyi", body="Tekrar yazıyorum"),
                    fake_user,
                    fake_session,
                )
            )

        self.assertEqual(exc.exception.status_code, 409)

    def test_delete_review_as_owner_success(self):
        review_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        fake_review = SimpleNamespace(id=review_id, user_id=owner_id, deleted_at=None)
        owner_user = SimpleNamespace(id=owner_id, role="user")

        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_review]),
            ]
        )

        self._run(review_service.delete_review(review_id, owner_user, fake_session))

        self.assertIsNotNone(fake_review.deleted_at)
        self.assertEqual(fake_session.commits, 1)

    def test_delete_review_forbidden_for_other_regular_user(self):
        review_id = uuid.uuid4()
        fake_review = SimpleNamespace(id=review_id, user_id=uuid.uuid4(), deleted_at=None)
        other_user = SimpleNamespace(id=uuid.uuid4(), role="user")

        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_review]),
            ]
        )

        with self.assertRaises(HTTPException) as exc:
            self._run(review_service.delete_review(review_id, other_user, fake_session))

        self.assertEqual(exc.exception.status_code, 403)

    def test_delete_review_admin_can_remove_any_review(self):
        review_id = uuid.uuid4()
        fake_review = SimpleNamespace(id=review_id, user_id=uuid.uuid4(), deleted_at=None)
        admin_user = SimpleNamespace(id=uuid.uuid4(), role="admin")

        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_review]),
            ]
        )

        self._run(review_service.delete_review(review_id, admin_user, fake_session))

        self.assertIsNotNone(fake_review.deleted_at)
        self.assertEqual(fake_session.commits, 1)

    def test_delete_review_moderator_can_remove_any_review(self):
        review_id = uuid.uuid4()
        fake_review = SimpleNamespace(id=review_id, user_id=uuid.uuid4(), deleted_at=None)
        moderator_user = SimpleNamespace(id=uuid.uuid4(), role="moderator")

        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_review]),
            ]
        )

        self._run(review_service.delete_review(review_id, moderator_user, fake_session))

        self.assertIsNotNone(fake_review.deleted_at)
        self.assertEqual(fake_session.commits, 1)

    def test_vote_insert_and_delete_flow(self):
        review_id = uuid.uuid4()
        user_id = uuid.uuid4()
        fake_review = SimpleNamespace(id=review_id, deleted_at=None)
        current_user = SimpleNamespace(id=user_id, role="user")

        fake_session_for_insert = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_review]),
                _FakeExecuteResult(scalars=[]),
            ]
        )
        self._run(
            review_service.upsert_review_vote(
                review_id,
                VoteCreate(vote="upvote"),
                current_user,
                fake_session_for_insert,
            )
        )
        self.assertEqual(len(fake_session_for_insert.added), 1)
        self.assertEqual(fake_session_for_insert.added[0].vote, "helpful")
        self.assertEqual(fake_session_for_insert.commits, 1)

        existing_vote = SimpleNamespace(id=uuid.uuid4(), review_id=review_id, user_id=user_id, vote="helpful")
        fake_session_for_update = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_review]),
                _FakeExecuteResult(scalars=[existing_vote]),
            ]
        )
        self._run(
            review_service.upsert_review_vote(
                review_id,
                VoteCreate(vote="downvote"),
                current_user,
                fake_session_for_update,
            )
        )
        self.assertEqual(existing_vote.vote, "unhelpful")
        self.assertEqual(fake_session_for_update.commits, 1)

        fake_session_for_delete = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[existing_vote]),
            ]
        )
        self._run(review_service.delete_review_vote(review_id, current_user, fake_session_for_delete))
        self.assertEqual(len(fake_session_for_delete.deleted), 1)
        self.assertEqual(fake_session_for_delete.commits, 1)


if __name__ == "__main__":
    unittest.main()

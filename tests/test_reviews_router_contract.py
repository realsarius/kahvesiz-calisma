import asyncio
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import Response

from app.routers import reviews
from app.schemas.review import ReviewCreate, VoteCreate


class ReviewsRouterContractTests(unittest.TestCase):
    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_list_reviews_uses_optional_auth_and_returns_payload(self):
        cafe_id = uuid.uuid4()
        fake_request = SimpleNamespace(headers={}, cookies={})
        fake_db = object()
        expected_payload = {"items": [], "next_cursor": None, "limit": 10, "total_count": 0}

        with patch.object(reviews.review_service, "get_current_user", new=AsyncMock(return_value=None)) as get_user_mock, patch.object(
            reviews.review_service,
            "list_reviews",
            new=AsyncMock(return_value=expected_payload),
        ) as list_reviews_mock:
            response = self._run(
                reviews.list_cafe_reviews(
                    cafe_id=cafe_id,
                    request=fake_request,
                    cursor=None,
                    limit=10,
                    db=fake_db,
                )
            )

        self.assertEqual(response, expected_payload)
        get_user_mock.assert_awaited_once_with(fake_request, fake_db, required=False)
        list_reviews_mock.assert_awaited_once_with(
            cafe_id=cafe_id,
            db=fake_db,
            limit=10,
            cursor=None,
            current_user=None,
        )

    def test_create_review_requires_auth_and_returns_created_review(self):
        cafe_id = uuid.uuid4()
        fake_request = SimpleNamespace(headers={}, cookies={})
        fake_db = object()
        fake_user = SimpleNamespace(id=uuid.uuid4(), role="user")
        fake_response = {
            "id": str(uuid.uuid4()),
            "user_id": str(fake_user.id),
            "cafe_id": str(cafe_id),
            "rating": 5,
            "title": "Harika",
            "body": "Gayet iyi",
            "noise_rating": 4,
            "wifi_rating": 5,
            "outlet_rating": 4,
            "visited_at": None,
            "is_verified_visit": False,
            "reviewer_name": "Deneme",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "my_vote": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        payload = ReviewCreate(rating=5, title="Harika", body="Gayet iyi")

        with patch.object(reviews.review_service, "get_current_user", new=AsyncMock(return_value=fake_user)) as get_user_mock, patch.object(
            reviews.review_service,
            "create_review",
            new=AsyncMock(return_value=fake_response),
        ) as create_review_mock:
            response = self._run(
                reviews.create_cafe_review(
                    cafe_id=cafe_id,
                    payload=payload,
                    request=fake_request,
                    db=fake_db,
                )
            )

        self.assertEqual(response, fake_response)
        get_user_mock.assert_awaited_once_with(fake_request, fake_db, required=True)
        create_review_mock.assert_awaited_once_with(
            cafe_id=cafe_id,
            payload=payload,
            current_user=fake_user,
            db=fake_db,
        )

    def test_delete_review_returns_204(self):
        review_id = uuid.uuid4()
        fake_request = SimpleNamespace(headers={}, cookies={})
        fake_db = object()
        fake_user = SimpleNamespace(id=uuid.uuid4(), role="admin")

        with patch.object(reviews.review_service, "get_current_user", new=AsyncMock(return_value=fake_user)) as get_user_mock, patch.object(
            reviews.review_service,
            "delete_review",
            new=AsyncMock(return_value=None),
        ) as delete_review_mock:
            response = self._run(
                reviews.remove_review(
                    review_id=review_id,
                    request=fake_request,
                    db=fake_db,
                )
            )

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 204)
        get_user_mock.assert_awaited_once_with(fake_request, fake_db, required=True)
        delete_review_mock.assert_awaited_once_with(
            review_id=review_id,
            current_user=fake_user,
            db=fake_db,
        )

    def test_vote_and_unvote_return_204(self):
        review_id = uuid.uuid4()
        fake_request = SimpleNamespace(headers={}, cookies={})
        fake_db = object()
        fake_user = SimpleNamespace(id=uuid.uuid4(), role="user")

        with patch.object(reviews.review_service, "get_current_user", new=AsyncMock(return_value=fake_user)), patch.object(
            reviews.review_service,
            "upsert_review_vote",
            new=AsyncMock(return_value=None),
        ) as upsert_vote_mock, patch.object(
            reviews.review_service,
            "delete_review_vote",
            new=AsyncMock(return_value=None),
        ) as delete_vote_mock:
            vote_response = self._run(
                reviews.vote_review(
                    review_id=review_id,
                    payload=VoteCreate(vote="upvote"),
                    request=fake_request,
                    db=fake_db,
                )
            )
            unvote_response = self._run(
                reviews.unvote_review(
                    review_id=review_id,
                    request=fake_request,
                    db=fake_db,
                )
            )

        self.assertEqual(vote_response.status_code, 204)
        self.assertEqual(unvote_response.status_code, 204)
        upsert_vote_mock.assert_awaited_once()
        delete_vote_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()

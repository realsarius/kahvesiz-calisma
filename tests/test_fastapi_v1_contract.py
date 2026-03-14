import asyncio
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import HTTPException, Response

from app.core.security import hash_token
from app.routers.auth import (
    logout,
    register_user,
    request_magic_link,
    verify_magic_link,
)
from app.routers.cafes import get_cafe, list_cafes
from app.routers.health import health_check
from app.schemas.auth import LogoutRequest, MagicLinkRequest, RegisterRequest, VerifyRequest


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
        raise ValueError("No scalar result present")


class _FakeAsyncSession:
    def __init__(self, execute_results=None):
        self._execute_results = list(execute_results or [])
        self.added = []
        self.deleted = []
        self.commits = 0
        self.refreshes = 0

    async def execute(self, _stmt):
        if not self._execute_results:
            return _FakeExecuteResult()
        return self._execute_results.pop(0)

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid.uuid4())
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, _obj):
        self.refreshes += 1

    async def rollback(self):
        return None

    async def delete(self, obj):
        self.deleted.append(obj)


class FastApiV1ContractTests(unittest.TestCase):
    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_health_endpoint_returns_ok(self):
        payload = self._run(health_check())
        self.assertEqual(payload, {"status": "ok"})

    def test_register_creates_user(self):
        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[]),  # existing user lookup
            ]
        )
        response = self._run(
            register_user(
                RegisterRequest(
                    email="new-user@example.com",
                    username="newuser",
                    display_name="New User",
                ),
                SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={}, cookies={}),
                fake_session,
            )
        )

        self.assertEqual(response.user.email, "new-user@example.com")
        self.assertEqual(response.user.username, "newuser")
        self.assertEqual(fake_session.commits, 1)
        self.assertGreaterEqual(len(fake_session.added), 1)

    def test_magic_link_returns_debug_token_in_development(self):
        fake_user = SimpleNamespace(
            id=uuid.uuid4(),
            email="magic@example.com",
            username="magic-user",
            display_name="Magic User",
            role="user",
            is_active=True,
            email_verified_at=None,
            deleted_at=None,
        )
        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_user]),  # user lookup
            ]
        )
        fake_request = SimpleNamespace(
            client=SimpleNamespace(host="127.0.0.1"),
            headers={},
            cookies={},
        )

        response = self._run(
            request_magic_link(
                MagicLinkRequest(email="magic@example.com"),
                fake_request,
                fake_session,
            )
        )

        self.assertEqual(response.status, "queued")
        self.assertIsNotNone(response.debug_token)
        self.assertEqual(fake_session.commits, 1)
        self.assertGreaterEqual(len(fake_session.added), 1)

    def test_verify_marks_token_used_and_creates_session(self):
        plain_token = "demo-plain-token"
        token_hash = hash_token(plain_token)
        fake_token = SimpleNamespace(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            token_hash=token_hash,
            token_type="magic_link",
            used_at=None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        fake_user = SimpleNamespace(
            id=fake_token.user_id,
            email="verify@example.com",
            username="verify-user",
            display_name="Verify User",
            role="user",
            is_active=True,
            email_verified_at=None,
            deleted_at=None,
        )
        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[fake_token]),  # token lookup
                _FakeExecuteResult(scalars=[fake_user]),  # user lookup
            ]
        )
        request = SimpleNamespace(
            client=SimpleNamespace(host="127.0.0.1"),
            headers={"user-agent": "unittest"},
            cookies={},
        )
        response = Response()

        payload = self._run(
            verify_magic_link(
                VerifyRequest(token=plain_token),
                request,
                response,
                fake_session,
            )
        )

        self.assertEqual(payload.message, "Giriş başarılı.")
        self.assertIsNotNone(fake_token.used_at)
        self.assertIsNotNone(fake_user.email_verified_at)
        self.assertEqual(fake_session.commits, 1)
        self.assertGreaterEqual(len(fake_session.added), 1)
        self.assertIn("set-cookie", {key.lower() for key in response.headers.keys()})

    def test_logout_requires_token(self):
        fake_session = _FakeAsyncSession()
        request = SimpleNamespace(
            headers={},
            cookies={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        response = Response()

        with self.assertRaises(HTTPException) as exc:
            self._run(logout(request, response, LogoutRequest(session_token=None), fake_session))
        self.assertEqual(exc.exception.status_code, 401)

    def test_cafes_list_returns_items_with_cursor(self):
        created_at = datetime.now(timezone.utc)
        row_1 = SimpleNamespace(
            Cafe=SimpleNamespace(
                id=uuid.uuid4(),
                name="Moda Brew",
                slug="moda-brew",
                address="Moda Cd. 1",
                latitude=40.98,
                longitude=29.12,
                avg_rating=4.5,
                review_count=10,
                created_at=created_at,
            ),
            neighborhood_name="Kadıköy",
            neighborhood_slug="kadikoy",
            wifi_available=True,
            noise_level="quiet",
        )
        row_2 = SimpleNamespace(
            Cafe=SimpleNamespace(
                id=uuid.uuid4(),
                name="Calm Cup",
                slug="calm-cup",
                address="Moda Cd. 2",
                latitude=40.97,
                longitude=29.11,
                avg_rating=4.1,
                review_count=7,
                created_at=created_at - timedelta(seconds=1),
            ),
            neighborhood_name="Kadıköy",
            neighborhood_slug="kadikoy",
            wifi_available=True,
            noise_level="silent",
        )
        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(scalars=[2]),
                _FakeExecuteResult(rows=[row_1, row_2]),
            ]
        )

        payload = self._run(
            list_cafes(
                cursor=None,
                limit=1,
                neighborhood="kadikoy",
                wifi=True,
                noise_level=None,
                has_outlet=None,
                db=fake_session,
            )
        )

        self.assertEqual(len(payload.items), 1)
        self.assertEqual(payload.items[0].slug, "moda-brew")
        self.assertIsNotNone(payload.next_cursor)
        self.assertEqual(payload.total_count, 2)

    def test_cafe_detail_returns_nested_payload(self):
        cafe = SimpleNamespace(
            id=uuid.uuid4(),
            name="Moda Brew",
            slug="moda-brew",
            description="Detay açıklama",
            address="Moda Cd. 1",
            latitude=40.98,
            longitude=29.12,
            phone=None,
            website=None,
            instagram=None,
            google_maps_url=None,
            is_verified=False,
            is_active=True,
            status="active",
            total_capacity=30,
            indoor_capacity=20,
            outdoor_capacity=10,
            avg_rating=4.5,
            review_count=12,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
        amenity = SimpleNamespace(
            wifi_available=True,
            wifi_speed_mbps=100,
            outlet_count=10,
            outlet_accessibility="some_seats",
            noise_level="quiet",
            has_natural_light=True,
            has_ac=True,
            has_heating=True,
            has_parking=False,
            has_accessible_entry=False,
            allows_laptop=True,
            min_spend_try=120,
            has_food=True,
            has_alcohol=False,
            pet_friendly=False,
        )
        detail_row = SimpleNamespace(
            Cafe=cafe,
            CafeAmenity=amenity,
            neighborhood_name="Kadıköy",
            neighborhood_slug="kadikoy",
        )
        hours = [SimpleNamespace(day_of_week=0, opens_at=None, closes_at=None, is_closed=True)]
        images = [SimpleNamespace(url="https://img.example.com/a.jpg", alt_text="A", is_primary=True, sort_order=0)]
        seats = [SimpleNamespace(seat_type="solo_desk", total_count=10, available_count=5, has_outlet=True, notes=None)]
        fake_session = _FakeAsyncSession(
            execute_results=[
                _FakeExecuteResult(rows=[detail_row]),
                _FakeExecuteResult(scalars=hours),
                _FakeExecuteResult(scalars=images),
                _FakeExecuteResult(scalars=seats),
            ]
        )

        payload = self._run(get_cafe("moda-brew", fake_session))
        self.assertEqual(payload.slug, "moda-brew")
        self.assertEqual(payload.neighborhood_slug, "kadikoy")
        self.assertEqual(len(payload.hours), 1)
        self.assertEqual(len(payload.images), 1)
        self.assertEqual(len(payload.seats), 1)


if __name__ == "__main__":
    unittest.main()

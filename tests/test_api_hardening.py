import os
import re
import unittest

TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_cafes.db"))

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["MAIL_PORT"] = "587"
os.environ["WTF_CSRF_ENABLED"] = "True"
os.environ["AUTO_CREATE_SCHEMA"] = "False"

import main  # noqa: E402
from kahvesiz_app.extensions import db  # noqa: E402
from kahvesiz_app.models import Cafe, User  # noqa: E402


class ApiHardeningTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        self.app = main.app
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            admin_user = User(
                name="Admin",
                email="admin@example.com",
                password="hashed-password",
                is_admin=True,
                is_confirmed=True,
            )
            regular_user = User(
                name="User",
                email="user@example.com",
                password="hashed-password",
                is_admin=False,
                is_confirmed=True,
            )
            db.session.add_all([admin_user, regular_user])
            db.session.commit()

            self.admin_id = admin_user.id
            self.user_id = regular_user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login_as(self, user_id):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True

    def _csrf_token(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)
        match = re.search(r'name="csrf-token" content="([^"]+)"', html)
        self.assertIsNotNone(match, "CSRF token meta tag bulunamadi")
        return match.group(1)

    @staticmethod
    def _cafe_payload(name="Test Cafe", details="<p>Test</p>"):
        return {
            "name": name,
            "map_url": f"https://maps.example.com/{name.replace(' ', '-').lower()}",
            "img_url": f"https://img.example.com/{name.replace(' ', '-').lower()}.jpg",
            "location": "Istanbul",
            "has_sockets": True,
            "has_toilet": True,
            "has_wifi": True,
            "can_take_calls": False,
            "seats": "20",
            "coffee_price": "120",
            "details": details,
        }

    def test_get_cafes_empty_returns_200_and_empty_list(self):
        response = self.client.get("/api/cafes")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["error"], None)
        self.assertEqual(payload["data"], {"cafes": []})

    def test_legacy_write_endpoints_are_removed(self):
        self.assertEqual(self.client.post("/api/add_cafe").status_code, 404)
        self.assertEqual(self.client.put("/api/update_cafe/1").status_code, 404)
        self.assertEqual(self.client.delete("/api/delete_cafe/1").status_code, 404)

    def test_post_cafe_without_csrf_token_is_rejected(self):
        self._login_as(self.admin_id)
        response = self.client.post(
            "/api/cafes",
            json=self._cafe_payload(),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("CSRF", payload["error"]["message"])

    def test_non_admin_cannot_create_cafe(self):
        self._login_as(self.user_id)
        csrf_token = self._csrf_token()
        response = self.client.post(
            "/api/cafes",
            json=self._cafe_payload(),
            headers={"Content-Type": "application/json", "X-CSRFToken": csrf_token},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"]["code"], "ADMIN_REQUIRED")

    def test_rich_text_is_sanitized_on_api_create(self):
        self._login_as(self.admin_id)
        csrf_token = self._csrf_token()
        response = self.client.post(
            "/api/cafes",
            json=self._cafe_payload(
                name="Sanitize Cafe",
                details='<script>alert("x")</script><p>Merhaba</p><a href="javascript:alert(1)">Link</a>',
            ),
            headers={"Content-Type": "application/json", "X-CSRFToken": csrf_token},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["error"], None)

        with self.app.app_context():
            cafe = Cafe.query.filter_by(name="Sanitize Cafe").first()
            self.assertIsNotNone(cafe)
            self.assertNotIn("<script", (cafe.details or "").lower())
            self.assertNotIn("javascript:", (cafe.details or "").lower())
            self.assertIn("<p>Merhaba</p>", cafe.details)

    def test_signup_duplicate_email_returns_409(self):
        csrf_token = self._csrf_token()
        response = self.client.post(
            "/api/signup",
            json={"name": "Another", "email": "user@example.com", "password": "12345678"},
            headers={"Content-Type": "application/json", "X-CSRFToken": csrf_token},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "EMAIL_ALREADY_EXISTS")

    def test_login_invalid_credentials_returns_401(self):
        csrf_token = self._csrf_token()
        response = self.client.post(
            "/api/login",
            json={"email": "user@example.com", "password": "wrong-password"},
            headers={"Content-Type": "application/json", "X-CSRFToken": csrf_token},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "INVALID_CREDENTIALS")


if __name__ == "__main__":
    unittest.main()

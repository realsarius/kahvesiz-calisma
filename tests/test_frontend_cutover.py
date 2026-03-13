import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_cafes_cutover.db"))

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["MAIL_PORT"] = "587"
os.environ["WTF_CSRF_ENABLED"] = "True"
os.environ["AUTO_CREATE_SCHEMA"] = "False"

import main  # noqa: E402


class FrontendCutoverTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        self.app = main.app
        self.client = self.app.test_client()
        self.original_dist = self.app.config.get("SOLID_DIST_DIR")
        self.temp_dist_dir = None

    def tearDown(self):
        self.app.config["SOLID_DIST_DIR"] = self.original_dist
        if self.temp_dist_dir and self.temp_dist_dir.exists():
            shutil.rmtree(self.temp_dist_dir, ignore_errors=True)

    def _login_as(self, user_id):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True

    def _make_temp_solid_dist(self):
        self.temp_dist_dir = Path(tempfile.mkdtemp(prefix="solid-dist-"))
        assets_dir = self.temp_dist_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        index_html = """
<!doctype html>
<html>
  <head><meta charset=\"utf-8\"><title>Solid Cutover</title></head>
  <body><div id=\"root\">solid-cutover-entry</div></body>
</html>
""".strip()
        (self.temp_dist_dir / "index.html").write_text(index_html, encoding="utf-8")
        (assets_dir / "app.js").write_text("console.log('solid-asset-ok');", encoding="utf-8")
        return self.temp_dist_dir

    def test_solid_mode_serves_spa_entry_and_assets(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/cafes")
        self.assertEqual(response.status_code, 200)
        self.assertIn("solid-cutover-entry", response.get_data(as_text=True))
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))
        response.close()

        asset_response = self.client.get("/solid/assets/app.js")
        self.assertEqual(asset_response.status_code, 200)
        self.assertIn("solid-asset-ok", asset_response.get_data(as_text=True))
        cache_header = asset_response.headers.get("Cache-Control", "")
        self.assertIn("max-age=31536000", cache_header)
        self.assertIn("immutable", cache_header)
        asset_response.close()

        index_alias = self.client.get("/index")
        self.assertEqual(index_alias.status_code, 200)
        self.assertIn("solid-cutover-entry", index_alias.get_data(as_text=True))
        index_alias.close()

        contact_alias = self.client.get("/contact_us")
        self.assertEqual(contact_alias.status_code, 200)
        self.assertIn("solid-cutover-entry", contact_alias.get_data(as_text=True))
        contact_alias.close()

    def test_solid_mode_serves_spa_entry_for_login_and_signup(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        login_page = self.client.get("/login")
        self.assertEqual(login_page.status_code, 200)
        self.assertIn("solid-cutover-entry", login_page.get_data(as_text=True))
        login_page.close()

        signup_page = self.client.get("/signup")
        self.assertEqual(signup_page.status_code, 200)
        self.assertIn("solid-cutover-entry", signup_page.get_data(as_text=True))
        signup_page.close()

    def test_solid_entry_includes_guest_auth_bootstrap_payload(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("window.__KAHVESIZ_AUTH__", html)
        self.assertIn('"isAuthenticated":false', html)
        self.assertIn('"user":null', html)
        response.close()

    def test_solid_entry_includes_authenticated_user_bootstrap_payload(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        class FakeUser:
            is_authenticated = True
            id = 77
            name = "Cutover User"
            email = "cutover@example.com"
            is_admin = False

        self._login_as(FakeUser.id)

        with patch("main.UserRepository.get_by_id", return_value=FakeUser()):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("window.__KAHVESIZ_AUTH__", html)
        self.assertIn('"isAuthenticated":true', html)
        self.assertIn('"email":"cutover@example.com"', html)
        self.assertIn('"name":"Cutover User"', html)
        response.close()

    def test_solid_mode_returns_503_if_dist_missing(self):
        self.app.config["SOLID_DIST_DIR"] = "/tmp/does-not-exist-solid-dist"

        response = self.client.get("/")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Solid frontend build bulunamadi", response.get_data(as_text=True))
        response.close()

    def test_solid_mode_catchall_serves_spa_entry_for_unknown_frontend_route(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/new-public-path")
        self.assertEqual(response.status_code, 200)
        self.assertIn("solid-cutover-entry", response.get_data(as_text=True))
        response.close()

    def test_solid_mode_catchall_does_not_intercept_api_namespace(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/api/unknown-endpoint")
        self.assertEqual(response.status_code, 404)
        response.close()

    def test_solid_mode_catchall_does_not_intercept_asset_like_paths(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/missing.js")
        self.assertEqual(response.status_code, 404)
        response.close()

    def test_solid_mode_admin_route_redirects_unauthenticated_user_to_login(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))
        response.close()

    def test_solid_mode_admin_route_serves_spa_entry_for_admin_user(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        class FakeAdmin:
            is_authenticated = True
            id = 91
            name = "Solid Admin"
            email = "solid-admin@example.com"
            is_admin = True

        self._login_as(FakeAdmin.id)

        with patch("main.UserRepository.get_by_id", return_value=FakeAdmin()):
            response = self.client.get("/admin", follow_redirects=False)

        self.assertEqual(response.status_code, 200)
        self.assertIn("solid-cutover-entry", response.get_data(as_text=True))
        response.close()

    def test_solid_mode_admin_route_redirects_non_admin_user_to_home(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        class FakeUser:
            is_authenticated = True
            id = 92
            name = "Solid User"
            email = "solid-user@example.com"
            is_admin = False

        self._login_as(FakeUser.id)

        with patch("main.UserRepository.get_by_id", return_value=FakeUser()):
            response = self.client.get("/admin", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.headers.get("Location", ""))
        response.close()

    def test_solid_mode_login_signup_redirect_authenticated_user_to_home(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        class FakeUser:
            is_authenticated = True
            id = 120
            name = "Authed User"
            email = "authed-user@example.com"
            is_admin = False

        self._login_as(FakeUser.id)

        with patch("main.UserRepository.get_by_id", return_value=FakeUser()):
            login_response = self.client.get("/login", follow_redirects=False)
            signup_response = self.client.get("/signup", follow_redirects=False)

        self.assertEqual(login_response.status_code, 302)
        self.assertIn("/", login_response.headers.get("Location", ""))
        login_response.close()

        self.assertEqual(signup_response.status_code, 302)
        self.assertIn("/", signup_response.headers.get("Location", ""))
        signup_response.close()

    def test_contact_route_serves_solid_entry(self):
        dist_dir = self._make_temp_solid_dist()
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/contact", follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn("solid-cutover-entry", response.get_data(as_text=True))
        response.close()


if __name__ == "__main__":
    unittest.main()

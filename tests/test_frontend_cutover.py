import os
import shutil
import tempfile
import unittest
from pathlib import Path

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
        self.original_mode = self.app.config.get("FRONTEND_RENDER_MODE")
        self.original_dist = self.app.config.get("SOLID_DIST_DIR")
        self.temp_dist_dir = None

    def tearDown(self):
        self.app.config["FRONTEND_RENDER_MODE"] = self.original_mode
        self.app.config["SOLID_DIST_DIR"] = self.original_dist
        if self.temp_dist_dir and self.temp_dist_dir.exists():
            shutil.rmtree(self.temp_dist_dir, ignore_errors=True)

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

        self.app.config["FRONTEND_RENDER_MODE"] = "solid"
        self.app.config["SOLID_DIST_DIR"] = str(dist_dir)

        response = self.client.get("/cafes")
        self.assertEqual(response.status_code, 200)
        self.assertIn("solid-cutover-entry", response.get_data(as_text=True))
        response.close()

        asset_response = self.client.get("/solid/assets/app.js")
        self.assertEqual(asset_response.status_code, 200)
        self.assertIn("solid-asset-ok", asset_response.get_data(as_text=True))
        asset_response.close()

        index_alias = self.client.get("/index")
        self.assertEqual(index_alias.status_code, 200)
        self.assertIn("solid-cutover-entry", index_alias.get_data(as_text=True))
        index_alias.close()

        contact_alias = self.client.get("/contact_us")
        self.assertEqual(contact_alias.status_code, 200)
        self.assertIn("solid-cutover-entry", contact_alias.get_data(as_text=True))
        contact_alias.close()

    def test_solid_mode_falls_back_to_jinja_if_dist_missing(self):
        self.app.config["FRONTEND_RENDER_MODE"] = "solid"
        self.app.config["SOLID_DIST_DIR"] = "/tmp/does-not-exist-solid-dist"

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Verimli Çalışma Alanları", response.get_data(as_text=True))
        response.close()

    def test_contact_route_redirects_to_legacy_page_in_jinja_mode(self):
        self.app.config["FRONTEND_RENDER_MODE"] = "jinja"

        response = self.client.get("/contact", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/contact_us", response.headers.get("Location", ""))
        response.close()


if __name__ == "__main__":
    unittest.main()

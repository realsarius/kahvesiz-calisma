import asyncio
import unittest
from types import SimpleNamespace
from typing import Dict, Optional

from fastapi import Response

from app.middleware import csrf
from app.routers.auth import get_csrf_token


def _fake_request(
    *,
    method: str,
    path: str,
    cookies: Optional[Dict] = None,
    headers: Optional[Dict] = None,
):
    return SimpleNamespace(
        method=method,
        url=SimpleNamespace(path=path),
        cookies=cookies or {},
        headers=headers or {},
    )


class CsrfMiddlewareContractTests(unittest.TestCase):
    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_skips_csrf_when_no_session_cookie(self):
        request = _fake_request(
            method="POST",
            path="/api/v1/reviews/11111111-1111-1111-1111-111111111111/vote",
            cookies={},
            headers={},
        )

        result = csrf.validate_csrf_request(request)
        self.assertIsNone(result)

    def test_rejects_missing_token_when_session_exists(self):
        request = _fake_request(
            method="DELETE",
            path="/api/v1/reviews/11111111-1111-1111-1111-111111111111",
            cookies={"session_token": "session-demo", "csrf_token": "cookie-token"},
            headers={},
        )

        result = csrf.validate_csrf_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_rejects_mismatched_token(self):
        request = _fake_request(
            method="PATCH",
            path="/api/v1/users/me/consent",
            cookies={"session_token": "session-demo", "csrf_token": "cookie-token"},
            headers={"x-csrftoken": "header-token"},
        )

        result = csrf.validate_csrf_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_accepts_matching_token(self):
        request = _fake_request(
            method="POST",
            path="/api/v1/reviews/11111111-1111-1111-1111-111111111111/vote",
            cookies={"session_token": "session-demo", "csrf_token": "same-token"},
            headers={"x-csrftoken": "same-token"},
        )

        result = csrf.validate_csrf_request(request)
        self.assertIsNone(result)

    def test_auth_register_is_exempt_for_bootstrap_flow(self):
        request = _fake_request(
            method="POST",
            path="/api/v1/auth/register",
            cookies={"session_token": "session-demo"},
            headers={},
        )

        result = csrf.validate_csrf_request(request)
        self.assertIsNone(result)

    def test_safe_api_request_with_session_issues_csrf_cookie(self):
        request = _fake_request(
            method="GET",
            path="/api/v1/auth/session",
            cookies={"session_token": "session-demo"},
            headers={},
        )
        response = Response()

        csrf.ensure_csrf_cookie_for_request(request, response)

        header_keys = {key.lower() for key in response.headers.keys()}
        self.assertIn("set-cookie", header_keys)
        self.assertIn("csrf_token=", response.headers.get("set-cookie", ""))

    def test_get_csrf_endpoint_reuses_existing_cookie(self):
        request = _fake_request(
            method="GET",
            path="/api/v1/auth/csrf",
            cookies={"csrf_token": "existing-token"},
            headers={},
        )
        response = Response()

        payload = self._run(get_csrf_token(request, response))

        self.assertEqual(payload["csrf_token"], "existing-token")
        self.assertNotIn("set-cookie", {key.lower() for key in response.headers.keys()})

    def test_get_csrf_endpoint_sets_cookie_when_missing(self):
        request = _fake_request(
            method="GET",
            path="/api/v1/auth/csrf",
            cookies={},
            headers={},
        )
        response = Response()

        payload = self._run(get_csrf_token(request, response))

        self.assertTrue(payload["csrf_token"])
        self.assertIn("set-cookie", {key.lower() for key in response.headers.keys()})
        self.assertIn("csrf_token=", response.headers.get("set-cookie", ""))


if __name__ == "__main__":
    unittest.main()

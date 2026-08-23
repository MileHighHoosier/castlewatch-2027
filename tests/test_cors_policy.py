import os
import unittest
from unittest.mock import patch

from flask import Flask, jsonify
from flask_cors import CORS

from cors_policy import install_cors_enforcement, origin_is_allowed


class CorsPolicyTests(unittest.TestCase):
    def make_client(self):
        app = Flask(__name__)
        # Reproduce the legacy global Flask-CORS behavior that Section 2D must
        # narrow at the final response boundary.
        CORS(app)
        install_cors_enforcement(app)

        @app.route("/api/test", methods=["GET", "OPTIONS"])
        def test_endpoint():
            return jsonify({"status": "ok"})

        return app.test_client()

    def test_production_and_castlewatch_preview_origins_are_allowed(self):
        self.assertTrue(origin_is_allowed("https://castlewatch-frontend.vercel.app"))
        self.assertTrue(origin_is_allowed("https://castlewatch-frontend-castlewatch.vercel.app"))
        self.assertTrue(origin_is_allowed(
            "https://castlewatch-frontend-git-rebaseline-section-2d-castlewatch.vercel.app"
        ))

    def test_unrelated_vercel_and_web_origins_are_rejected(self):
        self.assertFalse(origin_is_allowed("https://example.com"))
        self.assertFalse(origin_is_allowed("https://castlewatch-attacker.vercel.app"))
        self.assertFalse(origin_is_allowed("https://other-project-git-main-castlewatch.vercel.app"))

    def test_explicit_environment_origin_supports_local_development(self):
        with patch.dict(os.environ, {
            "CASTLEWATCH_ALLOWED_ORIGINS": "http://localhost:3000, https://staging.example.test/",
        }, clear=False):
            self.assertTrue(origin_is_allowed("http://localhost:3000"))
            self.assertTrue(origin_is_allowed("https://staging.example.test"))

    def test_allowed_origin_receives_explicit_cors_headers(self):
        client = self.make_client()
        response = client.get(
            "/api/test",
            headers={"Origin": "https://castlewatch-frontend.vercel.app"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://castlewatch-frontend.vercel.app",
        )
        self.assertIn("GET", response.headers.get("Access-Control-Allow-Methods", ""))
        self.assertIn("Content-Type", response.headers.get("Access-Control-Allow-Headers", ""))
        self.assertNotEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIsNone(response.headers.get("Access-Control-Allow-Credentials"))

    def test_disallowed_origin_has_legacy_cors_headers_removed(self):
        client = self.make_client()
        response = client.get(
            "/api/test",
            headers={"Origin": "https://evil.example"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        self.assertIsNone(response.headers.get("Access-Control-Allow-Methods"))
        self.assertIsNone(response.headers.get("Access-Control-Allow-Headers"))

    def test_disallowed_preflight_has_no_cors_grant(self):
        client = self.make_client()
        response = client.options(
            "/api/test",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        self.assertIsNone(response.headers.get("Access-Control-Allow-Methods"))


if __name__ == "__main__":
    unittest.main()

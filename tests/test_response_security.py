import unittest

from response_security import GENERIC_SERVER_ERROR_MESSAGE, sanitize_server_error_payload


class ResponseSecurityTests(unittest.TestCase):
    def test_non_server_error_is_unchanged(self):
        payload = {"status": "invalid_request", "message": "Missing field"}
        self.assertEqual(payload, sanitize_server_error_payload(payload, 400))

    def test_server_error_message_is_replaced(self):
        payload = {
            "status": "error",
            "message": "psycopg2 connection details should not escape",
            "source": "weather.gov",
        }
        sanitized = sanitize_server_error_payload(payload, 500)

        self.assertEqual("error", sanitized["status"])
        self.assertEqual("weather.gov", sanitized["source"])
        self.assertEqual(GENERIC_SERVER_ERROR_MESSAGE, sanitized["message"])
        self.assertNotIn("psycopg2", sanitized["message"])

    def test_non_dictionary_payload_is_unchanged(self):
        self.assertEqual("server error", sanitize_server_error_payload("server error", 500))


if __name__ == "__main__":
    unittest.main()

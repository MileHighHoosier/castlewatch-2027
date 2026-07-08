import re
import unittest

from accounts_auth import (
    DEVICE_TOKEN_KIND,
    INVITE_TOKEN_KIND,
    can_manage_devices,
    can_read_shared_plan,
    can_view_operations,
    can_write_shared_plan,
    generate_access_token,
    hash_access_token,
    normalize_display_name,
    normalize_role,
    parse_access_token,
    redact_access_token,
    safe_device_record,
    safe_invite_record,
    verify_access_token,
)


class AccountAuthHelperTests(unittest.TestCase):
    def test_generated_device_and_invite_tokens_are_parseable(self):
        device_token = generate_access_token(DEVICE_TOKEN_KIND)
        invite_token = generate_access_token(INVITE_TOKEN_KIND)

        device = parse_access_token(device_token, expected_kind=DEVICE_TOKEN_KIND)
        invite = parse_access_token(invite_token, expected_kind=INVITE_TOKEN_KIND)

        self.assertIsNotNone(device)
        self.assertIsNotNone(invite)
        self.assertEqual(device.kind, "device")
        self.assertEqual(invite.kind, "invite")
        self.assertRegex(device_token, r"^cwdev_[A-Za-z0-9_-]{6,24}_[A-Za-z0-9_-]{24,}$")
        self.assertRegex(invite_token, r"^cwinv_[A-Za-z0-9_-]{6,24}_[A-Za-z0-9_-]{24,}$")
        self.assertNotEqual(device.lookup_prefix, invite.lookup_prefix)

    def test_parser_rejects_wrong_kind_and_malformed_tokens(self):
        device_token = generate_access_token(DEVICE_TOKEN_KIND)

        self.assertIsNone(parse_access_token(device_token, expected_kind=INVITE_TOKEN_KIND))
        self.assertIsNone(parse_access_token("cwdev_missing-secret"))
        self.assertIsNone(parse_access_token("bad_kind_secret"))
        self.assertIsNone(parse_access_token("cwdev_short_short"))
        self.assertIsNone(parse_access_token(None))

    def test_hash_and_verify_token_without_storing_raw_secret(self):
        token = generate_access_token(DEVICE_TOKEN_KIND)
        token_hash = hash_access_token(token, "test-pepper")

        self.assertTrue(token_hash.startswith("sha256:"))
        self.assertNotIn(token, token_hash)
        self.assertNotIn(parse_access_token(token).lookup_prefix, token_hash)
        self.assertTrue(verify_access_token(token, token_hash, "test-pepper", expected_kind=DEVICE_TOKEN_KIND))
        self.assertFalse(verify_access_token(token, token_hash, "wrong-pepper", expected_kind=DEVICE_TOKEN_KIND))
        self.assertFalse(verify_access_token(token, token_hash, "test-pepper", expected_kind=INVITE_TOKEN_KIND))
        self.assertFalse(verify_access_token("invalid", token_hash, "test-pepper"))
        self.assertFalse(verify_access_token(token, "not-a-hash", "test-pepper"))

    def test_redaction_keeps_only_safe_lookup_prefix(self):
        token = generate_access_token(INVITE_TOKEN_KIND)
        parsed = parse_access_token(token)
        redacted = redact_access_token(token)

        self.assertEqual(redacted, f"cwinv_{parsed.lookup_prefix}_…")
        secret = token.split("_")[2]
        self.assertNotIn(secret, redacted)
        self.assertEqual(redact_access_token("not valid"), "invalid-token")

    def test_role_helpers_match_initial_authorization_plan(self):
        self.assertEqual(normalize_role(" OWNER "), "owner")
        self.assertIsNone(normalize_role("admin"))
        self.assertTrue(can_read_shared_plan("viewer"))
        self.assertTrue(can_write_shared_plan("editor"))
        self.assertFalse(can_write_shared_plan("viewer"))
        self.assertTrue(can_manage_devices("owner"))
        self.assertFalse(can_manage_devices("editor"))
        self.assertTrue(can_view_operations("owner"))
        self.assertTrue(can_view_operations("editor"))
        self.assertFalse(can_view_operations("viewer"))

    def test_display_name_normalization(self):
        self.assertEqual(normalize_display_name("  Ryan   iPhone  "), "Ryan iPhone")
        self.assertEqual(normalize_display_name("   "), "Unnamed device")
        self.assertEqual(len(normalize_display_name("x" * 100)), 80)

    def test_safe_records_do_not_expose_hashes_or_raw_tokens(self):
        token = generate_access_token(DEVICE_TOKEN_KIND)
        token_hash = hash_access_token(token, "pepper")
        row = {
            "id": "device-1",
            "display_name": "  Katie   iPhone  ",
            "role": "editor",
            "status": "active",
            "token_prefix": parse_access_token(token).lookup_prefix,
            "token_hash": token_hash,
            "raw_token": token,
            "created_at": "created",
            "last_seen_at": "seen",
            "last_read_at": "read",
            "last_write_at": "write",
            "revoked_at": None,
        }

        safe = safe_device_record(row)

        self.assertEqual(safe["displayName"], "Katie iPhone")
        self.assertEqual(safe["role"], "editor")
        self.assertEqual(safe["tokenPrefix"], parse_access_token(token).lookup_prefix)
        serialized = repr(safe)
        self.assertNotIn(token, serialized)
        self.assertNotIn(token_hash, serialized)
        self.assertNotIn("token_hash", safe)
        self.assertNotIn("raw_token", safe)

        invite = safe_invite_record({
            "id": "invite-1",
            "role": "viewer",
            "status": "open",
            "invite_prefix": "abc123",
            "invite_hash": "sha256:secret",
            "label": "  Katie invite  ",
            "expires_at": "expires",
            "created_at": "created",
            "accepted_at": None,
        })
        self.assertEqual(invite["label"], "Katie invite")
        self.assertNotIn("invite_hash", invite)

    def test_hash_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            hash_access_token("invalid", "pepper")
        with self.assertRaises(ValueError):
            hash_access_token(generate_access_token(DEVICE_TOKEN_KIND), "")


if __name__ == "__main__":
    unittest.main()

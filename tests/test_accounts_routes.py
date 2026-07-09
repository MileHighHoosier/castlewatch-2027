import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from flask import Flask

from accounts_access import DEVICE_TOKEN_HEADER, FAMILY_KEY_HEADER
from accounts_auth import DEVICE_TOKEN_KIND, generate_access_token, hash_access_token, parse_access_token
from accounts_routes import (
    accept_family_invite,
    check_family_device_access,
    create_family_invite,
    list_family_devices,
    rename_family_device,
    revoke_family_device,
)
from accounts_schema import FAMILY_WORKSPACE_ID


class FakeResult:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def mappings(self):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)


class FakeTransaction:
    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        return FakeConnection(self.engine)

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeEngine:
    def __init__(self):
        self.families = {}
        self.members = {}
        self.devices = {}
        self.invites = {}
        self.next_device = 1
        self.next_invite = 1

    def begin(self):
        return FakeTransaction(self)


class FakeConnection:
    def __init__(self, engine):
        self.engine = engine

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        parameters = parameters or {}

        if sql.startswith("create extension") or sql.startswith("create table") or sql.startswith("create index"):
            return FakeResult()

        if sql.startswith("insert into castlewatch_families"):
            family_id = parameters["family_id"]
            self.engine.families.setdefault(family_id, {
                "id": family_id,
                "display_name": parameters["display_name"],
                "legacy_family_key_enabled": True,
            })
            return FakeResult()

        if sql.startswith("insert into castlewatch_members"):
            member_id = parameters["member_id"]
            self.engine.members.setdefault(member_id, {
                "id": member_id,
                "family_id": parameters["family_id"],
                "display_name": parameters["display_name"],
                "role": "owner",
                "status": "active",
            })
            return FakeResult()

        if "from castlewatch_devices d" in sql and "where d.token_prefix" in sql:
            active_only = "and d.status = 'active'" in sql
            rows = []
            for device in self.engine.devices.values():
                if device["token_prefix"] != parameters["token_prefix"]:
                    continue
                if active_only and device["status"] != "active":
                    continue
                rows.append({
                    **device,
                    "member_status": None,
                })
            return FakeResult(rows)

        if sql.startswith("select") and "from castlewatch_devices" in sql and "where token_prefix" in sql:
            rows = [
                dict(device)
                for device in self.engine.devices.values()
                if device["token_prefix"] == parameters["token_prefix"]
            ]
            return FakeResult(rows)

        if sql.startswith("select") and "from castlewatch_devices" in sql and "id = cast(:device_id as uuid)" in sql:
            device = self.engine.devices.get(parameters["device_id"])
            if device and device["family_id"] == parameters["family_id"]:
                return FakeResult([dict(device)])
            return FakeResult()

        if sql.startswith("update castlewatch_devices") and "set last_seen_at" in sql:
            device = self.engine.devices.get(parameters["device_id"])
            if device:
                now = datetime.now(timezone.utc)
                device["last_seen_at"] = now
                if "last_read_at" in sql:
                    device["last_read_at"] = now
                if "last_write_at" in sql:
                    device["last_write_at"] = now
            return FakeResult()

        if sql.startswith("select") and "from castlewatch_devices" in sql and "where family_id" in sql:
            rows = [
                dict(device)
                for device in self.engine.devices.values()
                if device["family_id"] == parameters["family_id"]
            ]
            rows.sort(key=lambda row: row["created_at"], reverse=True)
            return FakeResult(rows)

        if sql.startswith("insert into castlewatch_invites"):
            invite_id = f"00000000-0000-0000-0000-0000000001{self.engine.next_invite:02d}"
            self.engine.next_invite += 1
            row = {
                "id": invite_id,
                "family_id": parameters["family_id"],
                "role": parameters["role"],
                "status": "open",
                "invite_hash": parameters["invite_hash"],
                "invite_prefix": parameters["invite_prefix"],
                "label": parameters["label"],
                "expires_at": parameters["expires_at"],
                "created_at": datetime.now(timezone.utc),
                "accepted_at": None,
                "accepted_device_id": None,
            }
            self.engine.invites[invite_id] = row
            return FakeResult([dict(row)])

        if "from castlewatch_invites" in sql and "where invite_prefix" in sql:
            rows = [
                dict(invite)
                for invite in self.engine.invites.values()
                if invite["invite_prefix"] == parameters["invite_prefix"] and invite["status"] == "open"
            ]
            return FakeResult(rows)

        if sql.startswith("insert into castlewatch_devices"):
            device_id = f"00000000-0000-0000-0000-0000000002{self.engine.next_device:02d}"
            self.engine.next_device += 1
            row = {
                "id": device_id,
                "family_id": parameters["family_id"],
                "member_id": None,
                "display_name": parameters["display_name"],
                "token_hash": parameters["token_hash"],
                "token_prefix": parameters["token_prefix"],
                "role": parameters["role"],
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "last_seen_at": datetime.now(timezone.utc),
                "last_read_at": None,
                "last_write_at": None,
                "revoked_at": None,
            }
            self.engine.devices[device_id] = row
            return FakeResult([dict(row)])

        if sql.startswith("update castlewatch_invites") and "set status = 'accepted'" in sql:
            invite = self.engine.invites.get(parameters["invite_id"])
            if invite:
                invite["status"] = "accepted"
                invite["accepted_at"] = datetime.now(timezone.utc)
                invite["accepted_device_id"] = parameters["device_id"]
            return FakeResult()

        if sql.startswith("update castlewatch_invites") and "set status = 'expired'" in sql:
            invite = self.engine.invites.get(parameters["invite_id"])
            if invite:
                invite["status"] = "expired"
            return FakeResult()

        if sql.startswith("update castlewatch_devices") and "set display_name" in sql:
            device = self.engine.devices.get(parameters["device_id"])
            if not device or device["family_id"] != parameters["family_id"] or device["status"] != "active":
                return FakeResult()
            device["display_name"] = parameters["display_name"]
            return FakeResult([dict(device)])

        if sql.startswith("update castlewatch_devices") and "set status = 'revoked'" in sql:
            device = self.engine.devices.get(parameters["device_id"])
            if not device or device["family_id"] != parameters["family_id"] or device["status"] != "active":
                return FakeResult()
            device["status"] = "revoked"
            device["revoked_at"] = datetime.now(timezone.utc)
            return FakeResult([dict(device)])

        raise AssertionError(f"Unexpected SQL in fake accounts engine: {sql}")


class AccountRouteTests(unittest.TestCase):
    key = "family-test-key"

    def setUp(self):
        self.app = Flask(__name__)
        self.engine = FakeEngine()
        self.environment = patch.dict(os.environ, {"CASTLEWATCH_FAMILY_KEY": self.key}, clear=False)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def invoke(self, handler, method="GET", body=None, headers=None):
        with self.app.test_request_context(
            "/api/family-trip/devices",
            method=method,
            json=body,
            headers=headers or {FAMILY_KEY_HEADER: self.key},
        ):
            result = handler(self.engine)
        if isinstance(result, tuple):
            response, status = result[0], result[1]
        else:
            response, status = result, result.status_code
        return status, response.get_json()

    def create_invite(self, role="editor", label="Katie iPhone"):
        return self.invoke(
            create_family_invite,
            method="POST",
            body={"role": role, "label": label},
        )

    def accept_invite(self, invite_token, device_name="Katie iPhone"):
        return self.invoke(
            accept_family_invite,
            method="POST",
            body={"inviteToken": invite_token, "deviceName": device_name},
            headers={},
        )

    def seed_owner_device(self):
        token = generate_access_token(DEVICE_TOKEN_KIND)
        parsed = parse_access_token(token, expected_kind=DEVICE_TOKEN_KIND)
        device_id = "00000000-0000-0000-0000-000000000299"
        self.engine.devices[device_id] = {
            "id": device_id,
            "family_id": FAMILY_WORKSPACE_ID,
            "member_id": None,
            "display_name": "Ryan iPhone",
            "token_hash": hash_access_token(token, self.key),
            "token_prefix": parsed.lookup_prefix,
            "role": "owner",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "last_seen_at": None,
            "last_read_at": None,
            "last_write_at": None,
            "revoked_at": None,
        }
        return token, device_id

    def test_legacy_key_creates_invite_without_exposing_hashes(self):
        status, result = self.create_invite(role="editor", label="  Katie   iPhone  ")

        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["inviteToken"].startswith("cwinv_"))
        self.assertEqual(result["invite"]["role"], "editor")
        self.assertEqual(result["invite"]["label"], "Katie iPhone")
        serialized = repr(result)
        self.assertNotIn("invite_hash", serialized)
        self.assertNotIn("token_hash", serialized)

    def test_family_key_access_state_is_explicit_owner_path(self):
        status, result = self.invoke(check_family_device_access)

        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["authState"], "family_key")
        self.assertEqual(result["role"], "owner")
        self.assertTrue(result["canManageDevices"])
        self.assertTrue(result["canWriteSharedPlan"])
        self.assertTrue(result["migrationRecommended"])
        self.assertIsNone(result["device"])

    def test_accept_invite_creates_device_token_once(self):
        _, invite = self.create_invite(role="editor")
        status, accepted = self.accept_invite(invite["inviteToken"], "Katie iPhone")

        self.assertEqual(status, 200)
        self.assertEqual(accepted["status"], "ok")
        self.assertTrue(accepted["deviceToken"].startswith("cwdev_"))
        self.assertEqual(accepted["device"]["displayName"], "Katie iPhone")
        self.assertEqual(accepted["device"]["role"], "editor")
        self.assertNotIn("token_hash", repr(accepted))
        self.assertNotIn(accepted["deviceToken"], repr(accepted["device"]))

    def test_editor_device_access_state_is_explicit_without_manage_permission(self):
        _, invite = self.create_invite(role="editor")
        _, accepted = self.accept_invite(invite["inviteToken"], "Katie iPhone")

        status, result = self.invoke(
            check_family_device_access,
            headers={DEVICE_TOKEN_HEADER: accepted["deviceToken"]},
        )

        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["authState"], "device_token")
        self.assertEqual(result["role"], "editor")
        self.assertFalse(result["canManageDevices"])
        self.assertTrue(result["canWriteSharedPlan"])
        self.assertFalse(result["migrationRecommended"])
        self.assertEqual(result["device"]["displayName"], "Katie iPhone")
        self.assertNotIn("token_hash", repr(result))

    def test_editor_device_cannot_manage_devices(self):
        _, invite = self.create_invite(role="editor")
        _, accepted = self.accept_invite(invite["inviteToken"], "Katie iPhone")

        status, result = self.invoke(
            list_family_devices,
            headers={DEVICE_TOKEN_HEADER: accepted["deviceToken"]},
        )

        self.assertEqual(status, 403)
        self.assertEqual(result["status"], "forbidden")

    def test_revoked_device_access_state_is_explicit_and_reconnectable(self):
        _, invite = self.create_invite(role="editor")
        _, accepted = self.accept_invite(invite["inviteToken"], "Katie iPhone")
        device_id = accepted["device"]["id"]

        status, revoked = self.invoke(
            revoke_family_device,
            method="POST",
            body={"deviceId": device_id},
        )
        self.assertEqual(status, 200)
        self.assertEqual(revoked["device"]["status"], "revoked")

        status, result = self.invoke(
            check_family_device_access,
            headers={DEVICE_TOKEN_HEADER: accepted["deviceToken"]},
        )

        self.assertEqual(status, 401)
        self.assertEqual(result["status"], "revoked")
        self.assertEqual(result["authState"], "revoked_device_token")
        self.assertEqual(result["device"]["status"], "revoked")
        self.assertFalse(result["canManageDevices"])
        self.assertFalse(result["canWriteSharedPlan"])
        self.assertIn("Reconnect", result["message"])
        self.assertNotIn("token_hash", repr(result))

    def test_owner_device_lists_renames_and_revokes_devices(self):
        owner_token, _ = self.seed_owner_device()
        _, invite = self.create_invite(role="editor")
        _, accepted = self.accept_invite(invite["inviteToken"], "Katie iPhone")
        device_id = accepted["device"]["id"]

        status, listed = self.invoke(
            list_family_devices,
            headers={DEVICE_TOKEN_HEADER: owner_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(listed["devices"]), 2)

        status, renamed = self.invoke(
            rename_family_device,
            method="POST",
            body={"deviceId": device_id, "displayName": "Katie new phone"},
            headers={DEVICE_TOKEN_HEADER: owner_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(renamed["device"]["displayName"], "Katie new phone")

        status, revoked = self.invoke(
            revoke_family_device,
            method="POST",
            body={"deviceId": device_id},
            headers={DEVICE_TOKEN_HEADER: owner_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(revoked["device"]["status"], "revoked")

        status, blocked = self.invoke(
            rename_family_device,
            method="POST",
            body={"deviceId": device_id, "displayName": "Should fail"},
            headers={DEVICE_TOKEN_HEADER: accepted["deviceToken"]},
        )
        self.assertEqual(status, 401)
        self.assertEqual(blocked["status"], "unauthorized")

    def test_viewer_invite_cannot_create_more_invites(self):
        _, invite = self.create_invite(role="viewer")
        _, accepted = self.accept_invite(invite["inviteToken"], "Grandma phone")

        status, result = self.invoke(
            create_family_invite,
            method="POST",
            body={"role": "viewer", "label": "Other phone"},
            headers={DEVICE_TOKEN_HEADER: accepted["deviceToken"]},
        )

        self.assertEqual(status, 403)
        self.assertEqual(result["status"], "forbidden")

    def test_expired_invite_is_rejected(self):
        _, invite = self.create_invite(role="editor")
        invite_id = next(iter(self.engine.invites))
        self.engine.invites[invite_id]["expires_at"] = datetime.now(timezone.utc) - timedelta(minutes=1)

        status, result = self.accept_invite(invite["inviteToken"], "Late phone")

        self.assertEqual(status, 410)
        self.assertEqual(result["status"], "expired")
        self.assertEqual(self.engine.invites[invite_id]["status"], "expired")


if __name__ == "__main__":
    unittest.main()

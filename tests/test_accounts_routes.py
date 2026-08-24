import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from accounts_access import DEVICE_TOKEN_HEADER, FAMILY_KEY_HEADER
from accounts_auth import DEVICE_TOKEN_KIND, generate_access_token, hash_access_token, parse_access_token
from accounts_routes import (
    accept_family_invite,
    bootstrap_family_owner_device,
    check_family_device_access,
    create_family_invite,
    list_family_devices,
    rename_family_device,
    revoke_family_device,
)
from accounts_schema import DEFAULT_OWNER_MEMBER_ID, FAMILY_WORKSPACE_ID


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

        if sql.startswith("select legacy_family_key_enabled"):
            family = self.engine.families.get(parameters["family_id"])
            return FakeResult([dict(family)] if family else [])

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

        if sql.startswith("select") and "from castlewatch_members" in sql and "for update" in sql:
            member = self.engine.members.get(parameters["member_id"])
            if (
                member
                and member["family_id"] == parameters["family_id"]
                and member["role"] == "owner"
                and member["status"] == "active"
            ):
                return FakeResult([dict(member)])
            return FakeResult()

        if (
            sql.startswith("select")
            and "from castlewatch_devices" in sql
            and "role = 'owner'" in sql
            and "status = 'active'" in sql
        ):
            rows = [
                dict(device)
                for device in self.engine.devices.values()
                if device["family_id"] == parameters["family_id"]
                and device["role"] == "owner"
                and device["status"] == "active"
            ]
            rows.sort(key=lambda row: row["created_at"])
            return FakeResult(rows[:1])

        if sql.startswith("select") and "from castlewatch_devices" in sql and "id = cast(:device_id as uuid)" in sql:
            device = self.engine.devices.get(parameters["device_id"])
            active_only = "status = 'active'" in sql
            if (
                device
                and device["family_id"] == parameters["family_id"]
                and (not active_only or device["status"] == "active")
            ):
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
                if "token_hash" in parameters:
                    device["token_hash"] = parameters["token_hash"]
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
                "member_id": parameters.get("member_id"),
                "display_name": parameters["display_name"],
                "token_hash": parameters["token_hash"],
                "token_prefix": parameters["token_prefix"],
                "role": parameters.get("role", "owner"),
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
        self.environment = patch.dict(os.environ, {
            "CASTLEWATCH_FAMILY_KEY": self.key,
            "CASTLEWATCH_DEVICE_TOKEN_PEPPER": "",
            "CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER": "",
        }, clear=False)
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
        return self.seed_device("owner", device_id="00000000-0000-0000-0000-000000000299")

    def seed_device(self, role="editor", status="active", pepper=None, device_id=None):
        token = generate_access_token(DEVICE_TOKEN_KIND)
        parsed = parse_access_token(token, expected_kind=DEVICE_TOKEN_KIND)
        device_id = device_id or f"00000000-0000-0000-0000-0000000003{len(self.engine.devices) + 1:02d}"
        self.engine.devices[device_id] = {
            "id": device_id,
            "family_id": FAMILY_WORKSPACE_ID,
            "member_id": None,
            "display_name": "Ryan iPhone" if role == "owner" else "Family device",
            "token_hash": hash_access_token(token, pepper or self.key),
            "token_prefix": parsed.lookup_prefix,
            "role": role,
            "status": status,
            "created_at": datetime.now(timezone.utc),
            "last_seen_at": None,
            "last_read_at": None,
            "last_write_at": None,
            "revoked_at": datetime.now(timezone.utc) if status == "revoked" else None,
        }
        return token, device_id

    def bootstrap_owner(self, device_name="Ryan iPhone", headers=None):
        return self.invoke(
            bootstrap_family_owner_device,
            method="POST",
            body={"deviceName": device_name},
            headers=headers,
        )

    def test_family_key_bootstraps_first_seeded_owner_device_once(self):
        status, result = self.bootstrap_owner("  Ryan's   iPhone  ")

        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["deviceToken"].startswith("cwdev_"))
        self.assertEqual(result["device"]["displayName"], "Ryan's iPhone")
        self.assertEqual(result["device"]["role"], "owner")
        device = next(iter(self.engine.devices.values()))
        self.assertEqual(device["member_id"], DEFAULT_OWNER_MEMBER_ID)
        self.assertEqual(self.engine.members[DEFAULT_OWNER_MEMBER_ID]["role"], "owner")
        self.assertTrue(self.engine.families[FAMILY_WORKSPACE_ID]["legacy_family_key_enabled"])
        self.assertNotIn("token_hash", repr(result))
        self.assertNotIn(result["deviceToken"], repr(result["device"]))

        token_status, token_access = self.invoke(
            check_family_device_access,
            headers={DEVICE_TOKEN_HEADER: result["deviceToken"]},
        )
        self.assertEqual(token_status, 200)
        self.assertEqual(token_access["authState"], "device_token")
        self.assertEqual(token_access["role"], "owner")
        self.assertTrue(token_access["canManageDevices"])

    def test_owner_bootstrap_rejects_repeat_without_returning_a_token(self):
        first_status, first = self.bootstrap_owner()
        self.assertEqual(first_status, 200)

        status, result = self.bootstrap_owner("Replacement")

        self.assertEqual(status, 409)
        self.assertEqual(result["status"], "owner_device_exists")
        self.assertEqual(result["device"]["id"], first["device"]["id"])
        self.assertNotIn("deviceToken", result)
        self.assertEqual(len(self.engine.devices), 1)

    def test_owner_bootstrap_requires_only_the_family_key(self):
        owner_token, _ = self.seed_owner_device()

        status, device_only = self.bootstrap_owner(headers={DEVICE_TOKEN_HEADER: owner_token})
        self.assertEqual(status, 401)
        self.assertEqual(device_only["status"], "unauthorized")

        status, multiple = self.bootstrap_owner(headers={
            FAMILY_KEY_HEADER: self.key,
            DEVICE_TOKEN_HEADER: owner_token,
        })
        self.assertEqual(status, 400)
        self.assertEqual(multiple["status"], "invalid_request")

        status, wrong = self.bootstrap_owner(headers={FAMILY_KEY_HEADER: "wrong-key"})
        self.assertEqual(status, 401)
        self.assertEqual(wrong["status"], "unauthorized")

    def test_owner_bootstrap_requires_json_and_an_active_seeded_owner(self):
        status, invalid = self.invoke(
            bootstrap_family_owner_device,
            method="POST",
            body=None,
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid["status"], "invalid_request")

        self.bootstrap_owner(headers={FAMILY_KEY_HEADER: "wrong-key"})
        self.engine.members[DEFAULT_OWNER_MEMBER_ID]["status"] = "disabled"
        status, unavailable = self.bootstrap_owner()
        self.assertEqual(status, 409)
        self.assertEqual(unavailable["status"], "bootstrap_unavailable")
        self.assertEqual(len(self.engine.devices), 0)

    def test_revoked_owner_device_allows_explicit_family_key_replacement(self):
        _, revoked_id = self.seed_owner_device()
        self.engine.devices[revoked_id]["status"] = "revoked"
        self.engine.devices[revoked_id]["revoked_at"] = datetime.now(timezone.utc)

        status, replacement = self.bootstrap_owner("Replacement owner")

        self.assertEqual(status, 200)
        self.assertEqual(replacement["device"]["role"], "owner")
        self.assertNotEqual(replacement["device"]["id"], revoked_id)
        self.assertEqual(len(self.engine.devices), 2)
        replacement_record = self.engine.devices[replacement["device"]["id"]]
        self.assertEqual(replacement_record["member_id"], DEFAULT_OWNER_MEMBER_ID)
        self.assertTrue(self.engine.families[FAMILY_WORKSPACE_ID]["legacy_family_key_enabled"])

    def test_production_app_registers_owner_bootstrap_route(self):
        source = Path(__file__).resolve().parents[1].joinpath("app.py").read_text()
        self.assertIn('from accounts_routes import (\n    bootstrap_family_owner_device,', source)
        self.assertIn('@app.route("/api/family-trip/devices/bootstrap-owner", methods=["POST"])', source)
        self.assertIn("return bootstrap_family_owner_device(engine)", source)

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

    def test_enabled_legacy_flag_is_authoritative_without_disabling_device_access(self):
        owner_token, owner_id = self.seed_owner_device()
        status, initial = self.invoke(check_family_device_access)
        self.assertEqual(status, 200)
        self.assertEqual(initial["authState"], "family_key")

        self.engine.families[FAMILY_WORKSPACE_ID]["legacy_family_key_enabled"] = False
        blocked_calls = (
            (check_family_device_access, "GET", None),
            (list_family_devices, "GET", None),
            (create_family_invite, "POST", {"role": "editor", "label": "Blocked invite"}),
            (rename_family_device, "POST", {"deviceId": owner_id, "displayName": "Blocked rename"}),
            (revoke_family_device, "POST", {"deviceId": owner_id}),
            (bootstrap_family_owner_device, "POST", {"deviceName": "Blocked bootstrap"}),
        )
        for handler, method, body in blocked_calls:
            status, result = self.invoke(handler, method=method, body=body)
            self.assertEqual(status, 403, handler.__name__)
            self.assertEqual(result["status"], "legacy_key_disabled", handler.__name__)

        self.assertEqual(self.engine.devices[owner_id]["display_name"], "Ryan iPhone")
        self.assertEqual(self.engine.devices[owner_id]["status"], "active")
        self.assertEqual(self.engine.invites, {})
        self.assertFalse(self.engine.families[FAMILY_WORKSPACE_ID]["legacy_family_key_enabled"])

        status, device_access = self.invoke(
            check_family_device_access,
            headers={DEVICE_TOKEN_HEADER: owner_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual(device_access["authState"], "device_token")
        status, listed = self.invoke(
            list_family_devices,
            headers={DEVICE_TOKEN_HEADER: owner_token},
        )
        self.assertEqual(status, 200)
        self.assertEqual([device["id"] for device in listed["devices"]], [owner_id])

    def test_revoked_device_is_denied_across_every_protected_device_route(self):
        revoked_token, revoked_id = self.seed_device("owner", status="revoked")
        _, target_id = self.seed_device("editor")
        original_target = dict(self.engine.devices[target_id])

        status, access = self.invoke(
            check_family_device_access,
            headers={DEVICE_TOKEN_HEADER: revoked_token},
        )
        self.assertEqual(status, 401)
        self.assertEqual(access["authState"], "revoked_device_token")
        self.assertEqual(access["device"]["id"], revoked_id)

        blocked_calls = (
            (list_family_devices, "GET", None),
            (create_family_invite, "POST", {"role": "editor", "label": "Blocked invite"}),
            (rename_family_device, "POST", {"deviceId": target_id, "displayName": "Blocked rename"}),
            (revoke_family_device, "POST", {"deviceId": target_id}),
            (bootstrap_family_owner_device, "POST", {"deviceName": "Blocked bootstrap"}),
        )
        for handler, method, body in blocked_calls:
            status, result = self.invoke(
                handler,
                method=method,
                body=body,
                headers={DEVICE_TOKEN_HEADER: revoked_token},
            )
            self.assertEqual(status, 401, handler.__name__)
            self.assertEqual(result["status"], "unauthorized", handler.__name__)

        self.assertEqual(self.engine.invites, {})
        self.assertEqual(self.engine.devices[target_id], original_target)

    def test_device_token_is_rehashed_when_a_stable_pepper_is_introduced(self):
        token, device_id = self.seed_device("owner", pepper=self.key)
        legacy_hash = self.engine.devices[device_id]["token_hash"]

        with patch.dict(os.environ, {"CASTLEWATCH_DEVICE_TOKEN_PEPPER": "stable-device-pepper"}):
            status, result = self.invoke(
                check_family_device_access,
                headers={DEVICE_TOKEN_HEADER: token},
            )

        self.assertEqual(status, 200)
        self.assertEqual(result["authState"], "device_token")
        self.assertNotEqual(self.engine.devices[device_id]["token_hash"], legacy_hash)
        self.assertEqual(
            self.engine.devices[device_id]["token_hash"],
            hash_access_token(token, "stable-device-pepper"),
        )

    def test_pepper_rotation_and_rollback_rehash_active_tokens(self):
        token, device_id = self.seed_device("owner", pepper="old-device-pepper")

        with patch.dict(os.environ, {
            "CASTLEWATCH_DEVICE_TOKEN_PEPPER": "new-device-pepper",
            "CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER": "old-device-pepper",
        }):
            status, _ = self.invoke(
                list_family_devices,
                headers={DEVICE_TOKEN_HEADER: token},
            )
        self.assertEqual(status, 200)
        self.assertEqual(
            self.engine.devices[device_id]["token_hash"],
            hash_access_token(token, "new-device-pepper"),
        )

        with patch.dict(os.environ, {
            "CASTLEWATCH_DEVICE_TOKEN_PEPPER": "old-device-pepper",
            "CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER": "new-device-pepper",
        }):
            status, _ = self.invoke(
                check_family_device_access,
                headers={DEVICE_TOKEN_HEADER: token},
            )
        self.assertEqual(status, 200)
        self.assertEqual(
            self.engine.devices[device_id]["token_hash"],
            hash_access_token(token, "old-device-pepper"),
        )

    def test_open_invite_survives_pepper_rotation_and_new_device_uses_primary(self):
        with patch.dict(os.environ, {"CASTLEWATCH_DEVICE_TOKEN_PEPPER": "old-device-pepper"}):
            status, invite = self.create_invite(role="viewer", label="Rotation invite")
        self.assertEqual(status, 200)

        with patch.dict(os.environ, {
            "CASTLEWATCH_DEVICE_TOKEN_PEPPER": "new-device-pepper",
            "CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER": "old-device-pepper",
        }):
            status, accepted = self.accept_invite(invite["inviteToken"], "Rotated device")

        self.assertEqual(status, 200)
        created = self.engine.devices[accepted["device"]["id"]]
        self.assertEqual(
            created["token_hash"],
            hash_access_token(accepted["deviceToken"], "new-device-pepper"),
        )

    def test_owner_revocation_requires_family_key_recovery_and_preserves_bootstrap(self):
        first_token, first_id = self.seed_owner_device()
        second_token, second_id = self.seed_device("owner")

        status, self_revoke = self.invoke(
            revoke_family_device,
            method="POST",
            body={"deviceId": first_id},
            headers={DEVICE_TOKEN_HEADER: first_token},
        )
        self.assertEqual(status, 400)
        self.assertEqual(self_revoke["status"], "invalid_request")

        status, peer_revoke = self.invoke(
            revoke_family_device,
            method="POST",
            body={"deviceId": first_id},
            headers={DEVICE_TOKEN_HEADER: second_token},
        )
        self.assertEqual(status, 409)
        self.assertEqual(peer_revoke["status"], "owner_recovery_required")
        self.assertEqual(self.engine.devices[first_id]["status"], "active")

        self.engine.devices[second_id]["status"] = "revoked"
        status, recovered = self.invoke(
            revoke_family_device,
            method="POST",
            body={"deviceId": first_id},
        )
        self.assertEqual(status, 200)
        self.assertTrue(recovered["recoveryRequired"])
        self.assertEqual(recovered["device"]["status"], "revoked")
        self.assertEqual(self.engine.members[DEFAULT_OWNER_MEMBER_ID]["status"], "active")
        self.assertTrue(self.engine.families[FAMILY_WORKSPACE_ID]["legacy_family_key_enabled"])

        status, replacement = self.bootstrap_owner("Replacement owner")
        self.assertEqual(status, 200)
        self.assertEqual(replacement["device"]["role"], "owner")
        self.assertNotEqual(replacement["device"]["id"], first_id)


if __name__ == "__main__":
    unittest.main()

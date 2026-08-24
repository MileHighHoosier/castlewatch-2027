import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from flask import Flask

import accounts_schema
import family_trip
import operations
from accounts_access import DEVICE_TOKEN_HEADER
from accounts_auth import (
    DEVICE_TOKEN_KIND,
    generate_access_token,
    hash_access_token,
    parse_access_token,
)


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
        self.state = None
        self.history = {}
        self.account_families = {}
        self.account_members = {}
        self.account_devices = {}
        self.schema_statements = []

    def begin(self):
        return FakeTransaction(self)


class FakeConnection:
    def __init__(self, engine):
        self.engine = engine

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        parameters = parameters or {}

        if sql.startswith("create extension") or sql.startswith("create table") or sql.startswith("create index"):
            self.engine.schema_statements.append(sql)
            return FakeResult()

        if (
            "insert into family_trip_history" in sql
            and "select id, version, payload, updated_at" in sql
        ):
            state = self.engine.state
            if state and state["version"] not in self.engine.history:
                self.engine.history[state["version"]] = {
                    "version": state["version"],
                    "payload": state["payload"],
                    "created_at": state["updated_at"],
                    "restored_from_version": None,
                }
            return FakeResult()

        if sql.startswith("insert into castlewatch_families"):
            family_id = parameters["family_id"]
            if family_id not in self.engine.account_families:
                self.engine.account_families[family_id] = {
                    "id": family_id,
                    "display_name": parameters["display_name"],
                    "legacy_family_key_enabled": True,
                }
            return FakeResult()

        if sql.startswith("insert into castlewatch_members"):
            member_id = parameters["member_id"]
            if member_id not in self.engine.account_members:
                self.engine.account_members[member_id] = {
                    "id": member_id,
                    "family_id": parameters["family_id"],
                    "display_name": parameters["display_name"],
                    "role": "owner",
                    "status": "active",
                }
            return FakeResult()

        if "from castlewatch_devices d" in sql and "where d.token_prefix" in sql:
            rows = [
                {
                    **device,
                    "member_status": None,
                }
                for device in self.engine.account_devices.values()
                if device["token_prefix"] == parameters["token_prefix"]
                and device["status"] == "active"
            ]
            return FakeResult(rows)

        if sql.startswith("update castlewatch_devices") and "set last_seen_at" in sql:
            device = self.engine.account_devices.get(parameters["device_id"])
            if device:
                now = datetime.now(timezone.utc)
                device["last_seen_at"] = now
                if "last_read_at" in sql:
                    device["last_read_at"] = now
                if "last_write_at" in sql:
                    device["last_write_at"] = now
            return FakeResult()

        if "select pg_advisory_xact_lock" in sql:
            return FakeResult()

        if sql.startswith("delete from family_trip_history"):
            limit = parameters.get("history_limit", family_trip.HISTORY_LIMIT)
            keep = sorted(self.engine.history, reverse=True)[:limit]
            self.engine.history = {
                version: self.engine.history[version]
                for version in keep
            }
            return FakeResult()

        if "select payload, version, updated_at" in sql and "from family_trip_state" in sql:
            return FakeResult([dict(self.engine.state)] if self.engine.state else [])

        if "select version" in sql and "from family_trip_state" in sql:
            if not self.engine.state:
                return FakeResult()
            return FakeResult([{"version": self.engine.state["version"]}])

        if (
            "select version, payload, created_at, restored_from_version" in sql
            and "from family_trip_history" in sql
            and "version = :version" in sql
        ):
            row = self.engine.history.get(parameters.get("version"))
            return FakeResult([dict(row)] if row else [])

        if (
            "select version, payload, created_at, restored_from_version" in sql
            and "from family_trip_history" in sql
        ):
            rows = [
                dict(self.engine.history[version])
                for version in sorted(self.engine.history, reverse=True)
            ]
            limit = parameters.get("history_limit", family_trip.HISTORY_LIMIT)
            return FakeResult(rows[:limit])

        if "select version, payload, created_at" in sql and "from family_trip_history" in sql:
            rows = [
                dict(self.engine.history[version])
                for version in sorted(self.engine.history, reverse=True)
            ]
            limit = parameters.get("history_limit", family_trip.HISTORY_LIMIT)
            return FakeResult(rows[:limit])

        if "select payload" in sql and "from family_trip_history" in sql:
            row = self.engine.history.get(parameters.get("version"))
            return FakeResult([{"payload": row["payload"]}] if row else [])

        if sql.startswith("insert into family_trip_state"):
            self.engine.state = {
                "payload": parameters["payload"],
                "version": parameters["version"],
                "updated_at": datetime.now(timezone.utc),
            }
            return FakeResult()

        if sql.startswith("update family_trip_state"):
            self.engine.state = {
                "payload": parameters["payload"],
                "version": parameters["version"],
                "updated_at": datetime.now(timezone.utc),
            }
            return FakeResult()

        if sql.startswith("insert into family_trip_history"):
            version = parameters["version"]
            if version not in self.engine.history:
                self.engine.history[version] = {
                    "version": version,
                    "payload": parameters["payload"],
                    "created_at": datetime.now(timezone.utc),
                    "restored_from_version": parameters.get("source_version"),
                }
            return FakeResult()

        raise AssertionError(f"Unexpected SQL in fake family-trip engine: {sql}")


class FamilyTripContractTests(unittest.TestCase):
    key = "family-test-key"

    def setUp(self):
        self.app = Flask(__name__)
        self.engine = FakeEngine()
        self.environment = patch.dict(
            os.environ,
            {"CASTLEWATCH_FAMILY_KEY": self.key},
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def payload(self, name):
        return {
            "schemaVersion": 1,
            "tripProfile": {
                "tripName": name,
                "startDate": "2027-10-09",
                "endDate": "2027-10-16",
            },
            "reservations": [],
            "resortPlan": {"2027-10-09": "value_tbd"},
            "approval": {"activeScenario": "base", "locked": False},
        }

    def invoke(self, handler, method="GET", path="/api/family-trip", body=None, headers=None):
        with self.app.test_request_context(
            path,
            method=method,
            json=body,
            headers=headers or {family_trip.FAMILY_KEY_HEADER: self.key},
        ):
            result = handler(self.engine)

        if isinstance(result, tuple):
            response, status = result[0], result[1]
        else:
            response, status = result, result.status_code
        return status, response.get_json()

    def write(self, expected_version, payload):
        return self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": expected_version, "payload": payload},
        )

    def seed_device(self, role, status="active", family_id=accounts_schema.FAMILY_WORKSPACE_ID):
        token = generate_access_token(DEVICE_TOKEN_KIND)
        parsed = parse_access_token(token, expected_kind=DEVICE_TOKEN_KIND)
        device_id = f"00000000-0000-0000-0000-000000000{len(self.engine.account_devices) + 101:03d}"
        self.engine.account_devices[device_id] = {
            "id": device_id,
            "family_id": family_id,
            "member_id": None,
            "role": role,
            "status": status,
            "token_hash": hash_access_token(token, self.key),
            "token_prefix": parsed.lookup_prefix,
            "last_seen_at": None,
            "last_read_at": None,
            "last_write_at": None,
        }
        return token, device_id

    def device_headers(self, token):
        return {DEVICE_TOKEN_HEADER: token}

    def test_additive_account_schema_setup_preserves_empty_shared_plan(self):
        status, downloaded = self.invoke(family_trip.get_family_trip)

        self.assertEqual(status, 200)
        self.assertEqual(downloaded["status"], "empty")
        self.assertIsNone(self.engine.state)
        self.assertEqual(self.engine.history, {})
        self.assertEqual(
            self.engine.account_families[accounts_schema.FAMILY_WORKSPACE_ID]["display_name"],
            accounts_schema.DEFAULT_FAMILY_DISPLAY_NAME,
        )
        owner = self.engine.account_members[accounts_schema.DEFAULT_OWNER_MEMBER_ID]
        self.assertEqual(owner["family_id"], accounts_schema.FAMILY_WORKSPACE_ID)
        self.assertEqual(owner["display_name"], accounts_schema.DEFAULT_OWNER_DISPLAY_NAME)
        self.assertEqual(owner["role"], "owner")
        self.assertEqual(owner["status"], "active")
        schema_sql = "\n".join(self.engine.schema_statements)
        self.assertIn("create table if not exists castlewatch_families", schema_sql)
        self.assertIn("create table if not exists castlewatch_members", schema_sql)
        self.assertIn("create table if not exists castlewatch_devices", schema_sql)
        self.assertIn("create table if not exists castlewatch_invites", schema_sql)

    def test_first_upload_and_download_round_trip(self):
        original = self.payload("First shared plan")

        status, saved = self.write(0, original)
        self.assertEqual(status, 200)
        self.assertEqual(saved["version"], 1)
        self.assertEqual(saved["payload"], original)

        status, downloaded = self.invoke(family_trip.get_family_trip)
        self.assertEqual(status, 200)
        self.assertEqual(downloaded["version"], 1)
        self.assertEqual(downloaded["payload"], original)

        status, history = self.invoke(
            family_trip.get_family_trip_history,
            path="/api/family-trip/history",
        )
        self.assertEqual(status, 200)
        self.assertEqual(history["currentVersion"], 1)
        self.assertEqual(len(history["entries"]), 1)
        self.assertTrue(history["entries"][0]["isCurrent"])

    def test_stale_write_preserves_the_current_server_document(self):
        first = self.payload("Version one")
        current = self.payload("Version two")
        stale = self.payload("Stale overwrite attempt")

        self.write(0, first)
        self.write(1, current)
        status, conflict = self.write(1, stale)

        self.assertEqual(status, 409)
        self.assertEqual(conflict["status"], "version_conflict")
        self.assertEqual(conflict["version"], 2)
        self.assertEqual(conflict["payload"], current)

        _, downloaded = self.invoke(family_trip.get_family_trip)
        self.assertEqual(downloaded["version"], 2)
        self.assertEqual(downloaded["payload"], current)

    def test_simultaneous_edits_allow_only_one_writer_from_the_same_baseline(self):
        base = self.payload("Shared baseline")
        browser_a = self.payload("Browser A edit")
        browser_b = self.payload("Browser B edit")

        self.write(0, base)
        first_status, first_saved = self.write(1, browser_a)
        second_status, second_result = self.write(1, browser_b)

        self.assertEqual(first_status, 200)
        self.assertEqual(first_saved["version"], 2)
        self.assertEqual(second_status, 409)
        self.assertEqual(second_result["payload"], browser_a)

    def test_restore_creates_a_new_version_without_erasing_history(self):
        version_one = self.payload("Version one")
        version_two = self.payload("Version two")

        self.write(0, version_one)
        self.write(1, version_two)
        status, restored = self.invoke(
            family_trip.restore_family_trip_version,
            method="POST",
            path="/api/family-trip/restore",
            body={"expectedVersion": 2, "sourceVersion": 1},
        )

        self.assertEqual(status, 200)
        self.assertEqual(restored["version"], 3)
        self.assertEqual(restored["payload"], version_one)
        self.assertEqual(restored["restoredFromVersion"], 1)

        _, history = self.invoke(
            family_trip.get_family_trip_history,
            path="/api/family-trip/history",
        )
        self.assertEqual(history["currentVersion"], 3)
        self.assertEqual([entry["version"] for entry in history["entries"]], [3, 2, 1])
        self.assertEqual(history["entries"][0]["restoredFromVersion"], 1)

    def test_wrong_family_key_is_rejected_before_storage_is_touched(self):
        with self.app.test_request_context(
            "/api/family-trip",
            headers={family_trip.FAMILY_KEY_HEADER: "wrong-key"},
        ):
            result = family_trip.get_family_trip(self.engine)

        response, status = result
        self.assertEqual(status, 401)
        self.assertEqual(response.get_json()["status"], "unauthorized")
        self.assertIsNone(self.engine.state)
        self.assertEqual(self.engine.account_families, {})
        self.assertEqual(self.engine.account_members, {})

    def test_device_roles_enforce_the_shared_plan_permission_matrix(self):
        first = self.payload("Version one")
        second = self.payload("Version two")
        self.write(0, first)
        self.write(1, second)
        owner_token, owner_id = self.seed_device("owner")
        editor_token, editor_id = self.seed_device("editor")
        viewer_token, viewer_id = self.seed_device("viewer")

        for token, device_id in (
            (owner_token, owner_id),
            (editor_token, editor_id),
            (viewer_token, viewer_id),
        ):
            headers = self.device_headers(token)
            status, document = self.invoke(family_trip.get_family_trip, headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(document["version"], 2)
            status, history = self.invoke(
                family_trip.get_family_trip_history,
                path="/api/family-trip/history",
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(history["currentVersion"], 2)
            status, snapshot = self.invoke(
                lambda engine: family_trip.get_family_trip_history_version(engine, 1),
                path="/api/family-trip/history/1",
                headers=headers,
            )
            self.assertEqual(status, 200)
            self.assertEqual(snapshot["version"], 1)
            self.assertIsNotNone(self.engine.account_devices[device_id]["last_read_at"])

        status, owner_saved = self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": 2, "payload": self.payload("Owner edit")},
            headers=self.device_headers(owner_token),
        )
        self.assertEqual(status, 200)
        self.assertEqual(owner_saved["version"], 3)
        self.assertIsNotNone(self.engine.account_devices[owner_id]["last_write_at"])

        status, editor_saved = self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": 3, "payload": self.payload("Editor edit")},
            headers=self.device_headers(editor_token),
        )
        self.assertEqual(status, 200)
        self.assertEqual(editor_saved["version"], 4)
        self.assertIsNotNone(self.engine.account_devices[editor_id]["last_write_at"])

        status, viewer_write = self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": 4, "payload": self.payload("Viewer edit")},
            headers=self.device_headers(viewer_token),
        )
        self.assertEqual(status, 403)
        self.assertEqual(viewer_write["status"], "forbidden")
        self.assertEqual(self.engine.state["version"], 4)
        self.assertIsNone(self.engine.account_devices[viewer_id]["last_write_at"])

        status, owner_restored = self.invoke(
            family_trip.restore_family_trip_version,
            method="POST",
            path="/api/family-trip/restore",
            body={"expectedVersion": 4, "sourceVersion": 1},
            headers=self.device_headers(owner_token),
        )
        self.assertEqual(status, 200)
        self.assertEqual(owner_restored["version"], 5)

        status, editor_restored = self.invoke(
            family_trip.restore_family_trip_version,
            method="POST",
            path="/api/family-trip/restore",
            body={"expectedVersion": 5, "sourceVersion": 2},
            headers=self.device_headers(editor_token),
        )
        self.assertEqual(status, 200)
        self.assertEqual(editor_restored["version"], 6)

        status, viewer_restore = self.invoke(
            family_trip.restore_family_trip_version,
            method="POST",
            path="/api/family-trip/restore",
            body={"expectedVersion": 6, "sourceVersion": 1},
            headers=self.device_headers(viewer_token),
        )
        self.assertEqual(status, 403)
        self.assertEqual(viewer_restore["status"], "forbidden")
        self.assertEqual(self.engine.state["version"], 6)

        for token in (owner_token, editor_token):
            status, report = self.invoke(
                operations.get_family_trip_operations,
                path="/api/family-trip/operations",
                headers=self.device_headers(token),
            )
            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "ok")

        status, viewer_operations = self.invoke(
            operations.get_family_trip_operations,
            path="/api/family-trip/operations",
            headers=self.device_headers(viewer_token),
        )
        self.assertEqual(status, 403)
        self.assertEqual(viewer_operations["status"], "forbidden")

    def test_device_credentials_reject_revoked_malformed_and_ambiguous_requests(self):
        active_token, _ = self.seed_device("owner")
        revoked_token, _ = self.seed_device("editor", status="revoked")
        other_family_token, _ = self.seed_device("owner", family_id="other-family")

        for token in (revoked_token, "cwdev_not-valid"):
            status, result = self.invoke(
                family_trip.get_family_trip,
                headers=self.device_headers(token),
            )
            self.assertEqual(status, 401)
            self.assertEqual(result["status"], "unauthorized")

        status, ambiguous = self.invoke(
            family_trip.get_family_trip,
            headers={
                family_trip.FAMILY_KEY_HEADER: self.key,
                DEVICE_TOKEN_HEADER: active_token,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(ambiguous["status"], "invalid_request")

        status, wrong_workspace = self.invoke(
            family_trip.get_family_trip,
            headers=self.device_headers(other_family_token),
        )
        self.assertEqual(status, 403)
        self.assertEqual(wrong_workspace["status"], "forbidden")

    def test_device_write_preserves_optimistic_conflict_and_history_contracts(self):
        editor_token, _ = self.seed_device("editor")
        headers = self.device_headers(editor_token)
        first = self.payload("Device version one")
        second = self.payload("Device version two")
        stale = self.payload("Stale device write")

        status, saved = self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": 0, "payload": first},
            headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(saved["version"], 1)

        status, saved = self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": 1, "payload": second},
            headers=headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(saved["version"], 2)

        status, conflict = self.invoke(
            family_trip.put_family_trip,
            method="PUT",
            body={"expectedVersion": 1, "payload": stale},
            headers=headers,
        )
        self.assertEqual(status, 409)
        self.assertEqual(conflict["status"], "version_conflict")
        self.assertEqual(conflict["payload"], second)
        self.assertEqual(sorted(self.engine.history), [1, 2])


if __name__ == "__main__":
    unittest.main()

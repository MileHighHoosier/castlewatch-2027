import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from flask import Flask

import family_trip


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

    def begin(self):
        return FakeTransaction(self)


class FakeConnection:
    def __init__(self, engine):
        self.engine = engine

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        parameters = parameters or {}

        if sql.startswith("create table") or sql.startswith("create index"):
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

    def invoke(self, handler, method="GET", path="/api/family-trip", body=None):
        with self.app.test_request_context(
            path,
            method=method,
            json=body,
            headers={family_trip.FAMILY_KEY_HEADER: self.key},
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


if __name__ == "__main__":
    unittest.main()

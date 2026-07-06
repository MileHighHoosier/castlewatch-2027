import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from flask import Flask

from family_trip import FAMILY_KEY_HEADER, MAX_PAYLOAD_BYTES
from operations import (
    RAILWAY_EGRESS_USD_PER_GIB,
    build_family_operations_report,
    get_family_trip_operations,
)


class FailingEngine:
    def begin(self):
        raise AssertionError("Unauthorized operations requests must not touch storage")


class FamilyOperationsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc)

    def test_empty_report_is_read_only_and_explicitly_estimated(self):
        report = build_family_operations_report(None, [], now=self.now)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["measurement"], "estimate_from_current_database_state")
        self.assertEqual(report["storage"]["currentVersion"], 0)
        self.assertEqual(report["storage"]["currentPayloadBytes"], 0)
        self.assertTrue(report["controls"]["readOnlyReport"])
        self.assertFalse(report["controls"]["telemetryRowsWritten"])
        self.assertIn("shared_plan_empty", [item["code"] for item in report["warnings"]])

    def test_report_counts_retained_recent_versions_and_sizes(self):
        payload = {
            "schemaVersion": 1,
            "tripProfile": {"tripName": "Columbus Day Week 2027"},
            "reservations": [{"id": "one", "title": "Dinner"}],
        }
        current = {
            "version": 12,
            "payload": payload,
            "updated_at": self.now - timedelta(minutes=5),
        }
        history = [
            {"version": 12, "payload": payload, "created_at": self.now - timedelta(hours=1)},
            {"version": 11, "payload": payload, "created_at": self.now - timedelta(days=2)},
            {"version": 10, "payload": payload, "created_at": self.now - timedelta(days=10)},
        ]

        report = build_family_operations_report(current, history, now=self.now)

        self.assertEqual(report["storage"]["currentVersion"], 12)
        self.assertGreater(report["storage"]["currentPayloadBytes"], 0)
        self.assertEqual(report["storage"]["retainedHistoryCount"], 3)
        self.assertEqual(report["activity"]["versionsCreatedLast24Hours"], 1)
        self.assertEqual(report["activity"]["versionsCreatedLast7Days"], 2)
        self.assertGreater(
            report["transferEstimates"]["estimatedRailwayEgressBytesPerGuardedAutosave"],
            report["transferEstimates"]["estimatedRailwayEgressBytesPerFullRead"],
        )
        self.assertEqual(
            report["pricingAssumptions"]["railwayNetworkEgressUsdPerGiB"],
            RAILWAY_EGRESS_USD_PER_GIB,
        )

    def test_large_payload_creates_a_limit_warning(self):
        payload = {"notes": "x" * int(MAX_PAYLOAD_BYTES * 0.82)}
        current = {
            "version": 3,
            "payload": payload,
            "updated_at": self.now,
        }

        report = build_family_operations_report(current, [], now=self.now)

        self.assertGreaterEqual(report["storage"]["payloadLimitUsedPercent"], 80)
        self.assertIn("payload_near_limit", [item["code"] for item in report["warnings"]])

    def test_high_version_churn_creates_a_warning(self):
        payload = {"schemaVersion": 1}
        history = [
            {
                "version": version,
                "payload": payload,
                "created_at": self.now - timedelta(minutes=version),
            }
            for version in range(1, 101)
        ]

        report = build_family_operations_report(
            {"version": 100, "payload": payload, "updated_at": self.now},
            history,
            now=self.now,
        )

        self.assertEqual(report["activity"]["versionsCreatedLast24Hours"], 100)
        self.assertIn("high_version_churn", [item["code"] for item in report["warnings"]])

    def test_wrong_family_key_is_rejected_before_storage_access(self):
        app = Flask(__name__)
        with patch.dict(os.environ, {"CASTLEWATCH_FAMILY_KEY": "correct-key"}, clear=False):
            with app.test_request_context(
                "/api/family-trip/operations",
                headers={FAMILY_KEY_HEADER: "wrong-key"},
            ):
                response, status = get_family_trip_operations(FailingEngine())

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json()["status"], "unauthorized")


if __name__ == "__main__":
    unittest.main()

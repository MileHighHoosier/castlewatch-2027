import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import calendar_ingestion
import special_events


def schedule_item(target_date, item_type, description, opening=None, closing=None):
    return {
        "date": target_date,
        "type": item_type,
        "description": description,
        "openingTime": opening,
        "closingTime": closing,
    }


def park_payload(park, *items):
    return {
        "park": park,
        "url": f"https://example.test/{park}",
        "schedule": list(items),
        "returned_items": len(items),
    }


def official_calendar_payload():
    return {
        "year": 2027,
        "month": 10,
        "park_schedules": {
            "Magic Kingdom": park_payload(
                "Magic Kingdom",
                schedule_item(
                    "2027-10-10",
                    "OPERATING",
                    "Park Open",
                    "2027-10-10T09:00:00-04:00",
                    "2027-10-10T18:00:00-04:00",
                ),
                schedule_item(
                    "2027-10-10",
                    "EVENT",
                    "Mickey's Not-So-Scary Halloween Party",
                    "2027-10-10T19:00:00-04:00",
                    "2027-10-11T00:00:00-04:00",
                ),
                schedule_item(
                    "2027-10-10",
                    "EXTRA_HOURS",
                    "Early Theme Park Entry",
                    "2027-10-10T08:30:00-04:00",
                    "2027-10-10T09:00:00-04:00",
                ),
            ),
            "Hollywood Studios": park_payload(
                "Hollywood Studios",
                schedule_item(
                    "2027-10-11",
                    "OPERATING",
                    "Park Open",
                    "2027-10-11T09:00:00-04:00",
                    "2027-10-11T21:00:00-04:00",
                ),
            ),
            "Epcot": park_payload(
                "Epcot",
                schedule_item(
                    "2027-10-13",
                    "OPERATING",
                    "Park Open",
                    "2027-10-13T09:00:00-04:00",
                    "2027-10-13T21:00:00-04:00",
                ),
                schedule_item(
                    "2027-10-13",
                    "EXTRA_HOURS",
                    "Extended Evening Hours",
                    "2027-10-13T21:00:00-04:00",
                    "2027-10-13T23:00:00-04:00",
                ),
            ),
            "Animal Kingdom": park_payload(
                "Animal Kingdom",
                schedule_item(
                    "2027-10-14",
                    "OPERATING",
                    "Park Open",
                    "2027-10-14T08:00:00-04:00",
                    "2027-10-14T19:00:00-04:00",
                ),
            ),
        },
    }


def calendar_status(
    party_dates=None,
    mnsshp_status="unreleased",
    hours_status="unreleased",
    ingestion_status="fresh",
):
    data = {
        "party_dates": list(party_dates or []),
        "mnsshp_status": mnsshp_status,
        "park_hours_status": hours_status,
        "park_hours": {},
        "early_entry": [],
        "extended_evening_hours": [],
        "relevant_park_dates_loaded": 4 if hours_status == "official" else 0,
        "relevant_park_dates_expected": 4,
    }
    return {
        "source": "Calendar contract fixture",
        "status": ingestion_status,
        "checked_at": "2026-08-23T12:00:00Z",
        "last_success_at": "2026-08-23T12:00:00Z",
        "last_changed_at": "2026-08-23T12:00:00Z",
        "changed": False,
        "error": None,
        "data": data,
    }


class CalendarIngestionContractTests(unittest.TestCase):
    def test_extracts_official_trip_hours_party_and_extra_hours(self):
        result = calendar_ingestion._extract_calendar_data(
            official_calendar_payload()
        )

        self.assertEqual(["2027-10-10"], result["party_dates"])
        self.assertEqual("official", result["mnsshp_status"])
        self.assertEqual("official", result["park_hours_status"])
        self.assertEqual(4, result["relevant_park_dates_loaded"])
        self.assertIn("Magic Kingdom|2027-10-10", result["park_hours"])
        self.assertEqual(
            "2027-10-10T18:00:00-04:00",
            result["park_hours"]["Magic Kingdom|2027-10-10"]["closingTime"],
        )
        self.assertEqual(1, len(result["early_entry"]))
        self.assertEqual(1, len(result["extended_evening_hours"]))

    def test_incomplete_source_data_stays_partial_and_party_schedule_unreleased(self):
        payload = official_calendar_payload()
        payload["park_schedules"] = {
            "Epcot": payload["park_schedules"]["Epcot"]
        }

        result = calendar_ingestion._extract_calendar_data(payload)

        self.assertEqual([], result["party_dates"])
        self.assertEqual("unreleased", result["mnsshp_status"])
        self.assertEqual("partial", result["park_hours_status"])
        self.assertEqual(1, result["relevant_park_dates_loaded"])

    def test_partial_refresh_merges_successes_with_last_known_failed_park(self):
        checked_at = datetime(2026, 8, 23, 12, 0, 0)
        old_animal_kingdom = park_payload(
            "Animal Kingdom",
            schedule_item(
                "2027-10-14",
                "OPERATING",
                "Park Open",
                "2027-10-14T08:00:00-04:00",
                "2027-10-14T19:00:00-04:00",
            ),
        )
        existing = {
            "payload": {"park_schedules": {"Animal Kingdom": old_animal_kingdom}},
            "content_hash": "old-hash",
            "last_checked_at": checked_at - timedelta(hours=25),
            "last_success_at": checked_at - timedelta(hours=25),
            "last_changed_at": checked_at - timedelta(hours=25),
            "last_error": None,
        }
        magic_kingdom = official_calendar_payload()["park_schedules"]["Magic Kingdom"]
        final_cache = {
            **existing,
            "payload": {
                "year": 2027,
                "month": 10,
                "park_schedules": {
                    "Animal Kingdom": old_animal_kingdom,
                    "Magic Kingdom": magic_kingdom,
                },
                "successful_parks": ["Magic Kingdom"],
                "failed_parks": ["Animal Kingdom"],
            },
            "last_checked_at": checked_at,
            "last_success_at": checked_at,
            "last_error": "Animal Kingdom: timeout",
        }

        with (
            patch.object(calendar_ingestion, "_utcnow", return_value=checked_at),
            patch.object(
                calendar_ingestion,
                "_read_cache",
                side_effect=[existing, final_cache],
            ),
            patch.object(
                calendar_ingestion,
                "_fetch_all_schedules",
                return_value=(
                    {"Magic Kingdom": magic_kingdom},
                    {"Animal Kingdom": "timeout"},
                ),
            ),
            patch.object(calendar_ingestion, "_write_success") as write_success,
        ):
            result = calendar_ingestion.refresh_calendar_ingestion(
                object(),
                force=True,
            )

        written_payload = write_success.call_args.args[1]
        self.assertIn("Animal Kingdom", written_payload["park_schedules"])
        self.assertIn("Magic Kingdom", written_payload["park_schedules"])
        self.assertEqual(["Animal Kingdom"], written_payload["failed_parks"])
        self.assertEqual("partial", result["status"])
        self.assertEqual("Animal Kingdom: timeout", result["error"])

    def test_total_refresh_failure_preserves_stale_last_known_schedule(self):
        checked_at = datetime(2026, 8, 23, 12, 0, 0)
        payload = official_calendar_payload()
        existing = {
            "payload": payload,
            "content_hash": calendar_ingestion._content_hash(payload),
            "last_checked_at": checked_at - timedelta(hours=48),
            "last_success_at": checked_at - timedelta(hours=48),
            "last_changed_at": checked_at - timedelta(hours=48),
            "last_error": None,
        }
        failed_cache = {
            **existing,
            "last_checked_at": checked_at,
            "last_error": "Magic Kingdom: source unavailable",
        }

        with (
            patch.object(calendar_ingestion, "_utcnow", return_value=checked_at),
            patch.object(
                calendar_ingestion,
                "_read_cache",
                side_effect=[existing, failed_cache],
            ),
            patch.object(
                calendar_ingestion,
                "_fetch_all_schedules",
                return_value=({}, {"Magic Kingdom": "source unavailable"}),
            ),
            patch.object(calendar_ingestion, "_write_failure") as write_failure,
        ):
            result = calendar_ingestion.refresh_calendar_ingestion(
                object(),
                force=True,
            )

        write_failure.assert_called_once_with(
            unittest.mock.ANY,
            checked_at,
            "Magic Kingdom: source unavailable",
        )
        self.assertEqual("stale", result["status"])
        self.assertEqual(["2027-10-10"], result["data"]["party_dates"])
        self.assertEqual("official", result["data"]["park_hours_status"])
        self.assertIn("source unavailable", result["error"])


class SpecialEventIntelligenceContractTests(unittest.TestCase):
    def intelligence_for(self, status):
        with (
            patch.dict(
                os.environ,
                {
                    "MNSSHP_2027_DATES": "",
                    "MNSSHP_2027_SCHEDULE_STATUS": "",
                    "WDW_2027_PARK_HOURS_STATUS": "",
                },
            ),
            patch.object(
                special_events,
                "get_calendar_ingestion_status",
                return_value=status,
            ),
        ):
            return special_events.get_special_event_intelligence(object())

    def test_unreleased_party_calendar_keeps_both_magic_kingdom_dates_provisional(self):
        result = self.intelligence_for(calendar_status())

        self.assertEqual("provisional", result["overall_status"])
        self.assertEqual("wait_for_calendar", result["recommendation"]["status"])
        self.assertEqual("base", result["recommendation"]["preferred_scenario"])
        signals = {
            item["date"]: item["signals"] for item in result["day_signals"]
        }
        sunday_party = next(
            signal for signal in signals["2027-10-10"] if signal["id"] == "mnsshp"
        )
        wednesday_party = next(
            signal for signal in signals["2027-10-13"] if signal["id"] == "mnsshp"
        )
        self.assertEqual("possible_event", sunday_party["status"])
        self.assertEqual("swap_date_unknown", wednesday_party["status"])

    def test_official_sunday_party_and_clear_wednesday_recommends_alternate(self):
        result = self.intelligence_for(
            calendar_status(
                party_dates=["2027-10-10"],
                mnsshp_status="official",
                hours_status="official",
            )
        )

        self.assertEqual("official", result["overall_status"])
        self.assertEqual("recommend_swap", result["recommendation"]["status"])
        self.assertEqual("alternate", result["recommendation"]["preferred_scenario"])

    def test_official_clear_sunday_keeps_base_plan(self):
        result = self.intelligence_for(
            calendar_status(
                party_dates=["2027-10-05"],
                mnsshp_status="official",
                hours_status="official",
            )
        )

        self.assertEqual("recommend_base", result["recommendation"]["status"])
        self.assertEqual("base", result["recommendation"]["preferred_scenario"])

    def test_party_on_both_swap_dates_requires_manual_review(self):
        result = self.intelligence_for(
            calendar_status(
                party_dates=["2027-10-10", "2027-10-13"],
                mnsshp_status="official",
                hours_status="official",
            )
        )

        self.assertEqual("manual_review", result["recommendation"]["status"])
        self.assertIn("Both Magic Kingdom options", result["recommendation"]["headline"])

    def test_stale_cached_calendar_is_not_reported_as_current_official_data(self):
        result = self.intelligence_for(
            calendar_status(
                party_dates=["2027-10-10"],
                mnsshp_status="official",
                hours_status="official",
                ingestion_status="stale",
            )
        )

        self.assertEqual("stale", result["overall_status"])
        self.assertTrue(all(source["status"] == "stale" for source in result["sources"]))
        self.assertTrue(all(source["data_status"] == "official" for source in result["sources"]))
        self.assertIn("cached schedule", result["sources"][0]["note"])


if __name__ == "__main__":
    unittest.main()

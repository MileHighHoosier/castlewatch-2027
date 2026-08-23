import unittest
from unittest.mock import patch

import trip_week


def forecast(park, target_date):
    return {
        "date": target_date,
        "park_marker": park,
        "status": "ready",
        "source": "same_weekday",
        "summary": f"Historical signal for {park} on {target_date}.",
        "confidence": {"level": "medium", "label": "Medium confidence"},
        "best_window": {"key": "morning", "window": "8:00–11:00 AM"},
        "peak_window": {"key": "afternoon", "window": "2:00–5:00 PM"},
    }


def event_intelligence():
    return {
        "overall_status": "official",
        "calendar_data": {},
        "calendar_ingestion": {
            "status": "fresh",
            "error": None,
        },
        "sources": [
            {
                "id": "mnsshp_calendar",
                "note": "Official schedule entries were detected automatically.",
            }
        ],
        "day_signals": [
            {
                "date": "2027-10-10",
                "signals": [
                    {
                        "id": "mnsshp",
                        "status": "confirmed_event",
                        "severity": "high",
                        "label": "Confirmed MNSSHP night",
                        "summary": "Regular day-guest hours end early.",
                    }
                ],
            },
            {
                "date": "2027-10-13",
                "signals": [
                    {
                        "id": "mnsshp",
                        "status": "confirmed_clear",
                        "severity": "low",
                        "label": "Magic Kingdom swap date is clear",
                        "summary": "Wednesday is clear.",
                    }
                ],
            },
        ],
        "scenarios": {},
        "recommendation": {
            "status": "recommend_swap",
            "preferred_scenario": "alternate",
        },
    }


class TripWeekContractTests(unittest.TestCase):
    def test_trip_week_attaches_forecasts_and_event_signals_to_exact_park_dates(self):
        forecasts = {
            (park, target_date): forecast(park, target_date)
            for park, target_date in trip_week._forecast_requests()
        }
        intelligence = event_intelligence()

        with (
            patch.object(trip_week, "_load_forecasts", return_value=forecasts),
            patch.object(
                trip_week,
                "get_special_event_intelligence",
                return_value=intelligence,
            ),
            patch.object(
                trip_week,
                "_force_calendar_refresh_requested",
                return_value=False,
            ),
        ):
            result = trip_week.get_trip_week_plan(object())

        self.assertEqual("2027-10-09", result["start_date"])
        self.assertEqual("2027-10-16", result["end_date"])
        self.assertEqual("provisional", result["status"])
        self.assertIn("No park hopping", result["constraints"])
        self.assertIn("Each park visited once", result["constraints"])

        base_sunday = next(
            day for day in result["days"] if day["date"] == "2027-10-10"
        )
        alternate_sunday = next(
            day
            for day in result["alternate_swap"]["days"]
            if day["date"] == "2027-10-10"
        )
        alternate_wednesday = next(
            day
            for day in result["alternate_swap"]["days"]
            if day["date"] == "2027-10-13"
        )

        self.assertEqual("Magic Kingdom", base_sunday["forecast"]["park_marker"])
        self.assertEqual("Epcot", alternate_sunday["forecast"]["park_marker"])
        self.assertEqual("Magic Kingdom", alternate_wednesday["forecast"]["park_marker"])
        self.assertEqual(
            "Sunday Magic Kingdom is a confirmed MNSSHP night",
            alternate_sunday["special_event_signals"][0]["label"],
        )
        self.assertEqual(
            "Confirmed MNSSHP night",
            intelligence["day_signals"][0]["signals"][0]["label"],
        )

    def test_one_forecast_failure_is_contained_and_does_not_expose_exception_text(self):
        def load(engine, park, target_date):
            if park == "Magic Kingdom":
                raise RuntimeError("INTERNAL-FORECAST-DETAIL-DO-NOT-EXPOSE")
            return forecast(park, target_date)

        with (
            patch.object(
                trip_week,
                "_forecast_requests",
                return_value=[
                    ("Magic Kingdom", "2027-10-10"),
                    ("Epcot", "2027-10-10"),
                ],
            ),
            patch.object(trip_week, "get_date_forecast", side_effect=load),
        ):
            result = trip_week._load_forecasts(object())

        unavailable = result[("Magic Kingdom", "2027-10-10")]
        self.assertEqual("unavailable", unavailable["status"])
        self.assertEqual("Forecast data could not be loaded.", unavailable["message"])
        self.assertNotIn("INTERNAL-FORECAST-DETAIL", str(unavailable))
        self.assertEqual("ready", result[("Epcot", "2027-10-10")]["status"])

    def test_calendar_failure_keeps_provisional_rules_without_exposing_exception_text(self):
        forecasts = {
            (park, target_date): forecast(park, target_date)
            for park, target_date in trip_week._forecast_requests()
        }
        original_intelligence = trip_week.get_special_event_intelligence

        def load_intelligence(engine=None, refresh_if_stale=True):
            if engine is not None:
                raise RuntimeError("INTERNAL-CALENDAR-DETAIL-DO-NOT-EXPOSE")
            return original_intelligence(
                engine=None,
                refresh_if_stale=refresh_if_stale,
            )

        with (
            patch.object(trip_week, "_load_forecasts", return_value=forecasts),
            patch.object(
                trip_week,
                "get_special_event_intelligence",
                side_effect=load_intelligence,
            ),
            patch.object(
                trip_week,
                "_force_calendar_refresh_requested",
                return_value=False,
            ),
        ):
            result = trip_week.get_trip_week_plan(object())

        intelligence = result["special_event_intelligence"]
        self.assertEqual("unavailable", intelligence["overall_status"])
        self.assertEqual("wait_for_calendar", intelligence["recommendation"]["status"])
        self.assertTrue(intelligence["degraded"])
        self.assertEqual(
            "Calendar intelligence is temporarily unavailable.",
            intelligence["degraded_reason"],
        )
        self.assertNotIn("INTERNAL-CALENDAR-DETAIL", str(result))
        self.assertIn("provisional", result["party_schedule_status"].lower())


if __name__ == "__main__":
    unittest.main()

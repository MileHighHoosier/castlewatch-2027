import unittest
from datetime import datetime
from types import SimpleNamespace

from live_planning_insights import get_live_planning_insights


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        self.statements.append(sql)
        if "with latest as" in sql:
            return list(self.rows)
        raise AssertionError(f"Unexpected SQL: {sql}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    def connect(self):
        return self.connection


def include_attraction(name):
    return not str(name).startswith("Skip")


class LivePlanningInsightsTests(unittest.TestCase):
    def test_history_total_and_comparisons_return_without_forecast_query(self):
        connection = FakeConnection([
            SimpleNamespace(
                ride_name="Ride A",
                land="World Celebration",
                samples=120,
                average_wait=35,
                peak_wait=70,
                same_hour_average=40,
                same_hour_samples=5,
                current_wait=15,
                is_open=True,
                current_updated_at=datetime(2026, 8, 22, 12, 0, 0),
            ),
            SimpleNamespace(
                ride_name="Ride B",
                land="World Nature",
                samples=80,
                average_wait=20,
                peak_wait=45,
                same_hour_average=18,
                same_hour_samples=4,
                current_wait=25,
                is_open=True,
                current_updated_at=datetime(2026, 8, 22, 12, 0, 0),
            ),
            SimpleNamespace(
                ride_name="Skip Show",
                land="World Showcase",
                samples=50,
                average_wait=5,
                peak_wait=10,
                same_hour_average=5,
                same_hour_samples=4,
                current_wait=5,
                is_open=True,
                current_updated_at=datetime(2026, 8, 22, 12, 0, 0),
            ),
        ])

        result = get_live_planning_insights(
            FakeEngine(connection),
            "Epcot",
            include_attraction,
        )

        self.assertEqual("Epcot", result["park"])
        self.assertEqual(200, result["historical_entries_analyzed"])
        self.assertEqual(2, result["rides_analyzed"])
        self.assertEqual("Ride A", result["best_now"][0]["name"])
        self.assertEqual(25, result["best_now"][0]["opportunity_score"])
        self.assertEqual("deferred", result["tomorrow_forecast"]["status"])
        self.assertEqual(1, len(connection.statements))
        self.assertNotIn("create table", connection.statements[0])
        self.assertNotIn("alter table", connection.statements[0])

    def test_closed_rides_still_count_toward_history_but_not_live_best_now(self):
        connection = FakeConnection([
            SimpleNamespace(
                ride_name="Ride A",
                land="Fantasyland",
                samples=30,
                average_wait=25,
                peak_wait=55,
                same_hour_average=25,
                same_hour_samples=5,
                current_wait=0,
                is_open=False,
                current_updated_at=datetime(2026, 8, 22, 12, 0, 0),
            ),
        ])

        result = get_live_planning_insights(
            FakeEngine(connection),
            "Magic Kingdom",
            include_attraction,
        )

        self.assertEqual(30, result["historical_entries_analyzed"])
        self.assertEqual([], result["best_now"])
        self.assertEqual([], result["reliable_low_wait"])


if __name__ == "__main__":
    unittest.main()

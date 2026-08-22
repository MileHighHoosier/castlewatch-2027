import unittest
from datetime import datetime
from types import SimpleNamespace

from planning_insights_fast import get_fast_historical_planning_insights


class FakeConnection:
    def __init__(self, count_rows, detail_rows=None, detail_error=None):
        self.count_rows = count_rows
        self.detail_rows = detail_rows or []
        self.detail_error = detail_error
        self.statements = []

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        self.statements.append(sql)

        if "select ride_name, count(*)::integer as samples" in sql:
            return list(self.count_rows)
        if sql.startswith("set local statement_timeout"):
            return []
        if "with latest as" in sql:
            if self.detail_error is not None:
                raise self.detail_error
            return list(self.detail_rows)
        raise AssertionError(f"Unexpected SQL: {sql}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeEngine:
    def __init__(self, connections):
        self.connections = list(connections)

    def connect(self):
        if not self.connections:
            raise AssertionError("No fake connection remaining")
        return self.connections.pop(0)


def include_attraction(name):
    return not str(name).startswith("Skip")


class PlanningInsightsFastTests(unittest.TestCase):
    def test_history_total_survives_detailed_query_timeout(self):
        count_connection = FakeConnection([
            SimpleNamespace(ride_name="Ride A", samples=120),
            SimpleNamespace(ride_name="Ride B", samples=80),
            SimpleNamespace(ride_name="Skip Show", samples=50),
        ])
        detail_connection = FakeConnection([], detail_error=TimeoutError("detail query timed out"))

        result = get_fast_historical_planning_insights(
            FakeEngine([count_connection, detail_connection]),
            "Epcot",
            include_attraction,
        )

        self.assertEqual(200, result["historical_entries_analyzed"])
        self.assertEqual("unavailable", result["detail_status"])
        self.assertEqual([], result["best_now"])
        self.assertEqual("deferred", result["tomorrow_forecast"]["status"])

    def test_ready_result_preserves_live_dashboard_comparisons(self):
        count_connection = FakeConnection([
            SimpleNamespace(ride_name="Ride A", samples=10),
        ])
        detail_connection = FakeConnection([], detail_rows=[
            SimpleNamespace(
                ride_name="Ride A",
                land="World Celebration",
                samples=10,
                average_wait=30,
                peak_wait=60,
                same_hour_average=40,
                same_hour_samples=4,
                current_wait=15,
                is_open=True,
                current_updated_at=datetime(2026, 8, 22, 5, 0, 0),
            ),
        ])

        result = get_fast_historical_planning_insights(
            FakeEngine([count_connection, detail_connection]),
            "Epcot",
            include_attraction,
        )

        self.assertEqual(10, result["historical_entries_analyzed"])
        self.assertEqual(1, result["rides_analyzed"])
        self.assertEqual("ready", result["detail_status"])
        self.assertEqual("Ride A", result["best_now"][0]["name"])
        self.assertEqual(25, result["best_now"][0]["opportunity_score"])
        self.assertEqual("deferred", result["tomorrow_forecast"]["status"])

    def test_count_query_filters_non_ride_samples(self):
        count_connection = FakeConnection([
            SimpleNamespace(ride_name="Ride A", samples=34),
            SimpleNamespace(ride_name="Skip Character", samples=99),
        ])
        detail_connection = FakeConnection([], detail_rows=[])

        result = get_fast_historical_planning_insights(
            FakeEngine([count_connection, detail_connection]),
            "Epcot",
            include_attraction,
        )

        self.assertEqual(34, result["historical_entries_analyzed"])


if __name__ == "__main__":
    unittest.main()

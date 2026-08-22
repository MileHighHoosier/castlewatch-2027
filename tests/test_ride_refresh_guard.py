import unittest
from datetime import datetime, timedelta

from ride_refresh_guard import guarded_collect_wait_times, refresh_is_due


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeConnection:
    def __init__(self, latest_values, lock_acquired=True, table_exists=True):
        self.latest_values = list(latest_values)
        self.lock_acquired = lock_acquired
        self.table_exists = table_exists
        self.statements = []

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        self.statements.append(sql)
        if "to_regclass" in sql:
            return ScalarResult("wait_times" if self.table_exists else None)
        if "max(created_at)" in sql:
            value = self.latest_values.pop(0) if self.latest_values else None
            return ScalarResult(value)
        if "pg_try_advisory_xact_lock" in sql:
            return ScalarResult(self.lock_acquired)
        raise AssertionError(f"Unexpected SQL: {sql}")


class FakeBegin:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return FakeBegin(self.connection)


class RideRefreshGuardTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 21, 21, 0, 0)

    def test_refresh_due_when_no_history_exists(self):
        self.assertTrue(refresh_is_due(None, self.now, 300))

    def test_refresh_not_due_inside_interval(self):
        self.assertFalse(refresh_is_due(self.now - timedelta(seconds=299), self.now, 300))
        self.assertTrue(refresh_is_due(self.now - timedelta(seconds=300), self.now, 300))

    def test_recent_refresh_skips_collection_before_lock(self):
        latest = self.now - timedelta(seconds=60)
        connection = FakeConnection([latest])
        collector_calls = []

        result = guarded_collect_wait_times(
            FakeEngine(connection),
            lambda: collector_calls.append(True),
            interval_seconds=300,
            now=self.now,
        )

        self.assertEqual("refresh_not_due", result["status"])
        self.assertFalse(result["refreshed"])
        self.assertEqual([], collector_calls)
        self.assertFalse(any("pg_try_advisory_xact_lock" in sql for sql in connection.statements))

    def test_concurrent_refresh_skips_when_lock_is_busy(self):
        latest = self.now - timedelta(seconds=600)
        connection = FakeConnection([latest], lock_acquired=False)
        collector_calls = []

        result = guarded_collect_wait_times(
            FakeEngine(connection),
            lambda: collector_calls.append(True),
            interval_seconds=300,
            now=self.now,
        )

        self.assertEqual("refresh_in_progress", result["status"])
        self.assertFalse(result["refreshed"])
        self.assertEqual([], collector_calls)

    def test_stale_refresh_collects_once_after_lock(self):
        latest = self.now - timedelta(seconds=600)
        connection = FakeConnection([latest, latest], lock_acquired=True)
        collector_calls = []

        def collect():
            collector_calls.append(True)
            return {"inserted": 42, "updated_at": "2026-08-22T03:00:00Z"}

        result = guarded_collect_wait_times(
            FakeEngine(connection),
            collect,
            interval_seconds=300,
            now=self.now,
        )

        self.assertEqual("refreshed", result["status"])
        self.assertTrue(result["refreshed"])
        self.assertEqual(42, result["inserted"])
        self.assertEqual([True], collector_calls)

    def test_second_stale_check_prevents_duplicate_collection(self):
        old = self.now - timedelta(seconds=600)
        recent = self.now - timedelta(seconds=30)
        connection = FakeConnection([old, recent], lock_acquired=True)
        collector_calls = []

        result = guarded_collect_wait_times(
            FakeEngine(connection),
            lambda: collector_calls.append(True),
            interval_seconds=300,
            now=self.now,
        )

        self.assertEqual("refresh_not_due", result["status"])
        self.assertEqual([], collector_calls)


if __name__ == "__main__":
    unittest.main()

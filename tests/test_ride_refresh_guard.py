import unittest
from datetime import datetime, timedelta, timezone

from ride_refresh_guard import guarded_collect_wait_times, refresh_is_due


class ScalarResult:
    def __init__(self, value=None):
        self.value = value

    def scalar(self):
        return self.value


class FakeConnection:
    def __init__(
        self,
        *,
        state_last_refresh=None,
        wait_last_refresh=None,
        lock_acquired=True,
        table_exists=True,
    ):
        self.state_last_refresh = state_last_refresh
        self.wait_last_refresh = wait_last_refresh
        self.lock_acquired = lock_acquired
        self.table_exists = table_exists
        self.statements = []

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        parameters = parameters or {}
        self.statements.append(sql)

        if sql.startswith("create table if not exists castlewatch_runtime_state"):
            return ScalarResult()
        if "pg_try_advisory_xact_lock" in sql:
            return ScalarResult(self.lock_acquired)
        if "select last_completed_at" in sql and "castlewatch_runtime_state" in sql:
            return ScalarResult(self.state_last_refresh)
        if "to_regclass" in sql:
            return ScalarResult("wait_times" if self.table_exists else None)
        if "max(created_at)" in sql:
            return ScalarResult(self.wait_last_refresh)
        if sql.startswith("insert into castlewatch_runtime_state"):
            self.state_last_refresh = parameters["completed_at"]
            return ScalarResult()

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
        self.now = datetime(2026, 8, 21, 21, 0, 0, tzinfo=timezone.utc)

    def test_refresh_due_when_no_history_exists(self):
        self.assertTrue(refresh_is_due(None, self.now, 300))

    def test_refresh_not_due_inside_interval(self):
        self.assertFalse(refresh_is_due(self.now - timedelta(seconds=299), self.now, 300))
        self.assertTrue(refresh_is_due(self.now - timedelta(seconds=300), self.now, 300))

    def test_concurrent_refresh_skips_when_lock_is_busy(self):
        connection = FakeConnection(
            state_last_refresh=self.now - timedelta(seconds=600),
            wait_last_refresh=self.now - timedelta(seconds=600),
            lock_acquired=False,
        )
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
        self.assertEqual("persistent-v2", result["refresh_guard"])

    def test_recent_persisted_refresh_skips_collection(self):
        recent = self.now - timedelta(seconds=60)
        connection = FakeConnection(
            state_last_refresh=recent,
            wait_last_refresh=self.now - timedelta(seconds=600),
        )
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
        self.assertEqual("persistent-v2", result["refresh_guard"])

    def test_recent_wait_timestamp_is_migration_fallback(self):
        recent = self.now - timedelta(seconds=30)
        connection = FakeConnection(state_last_refresh=None, wait_last_refresh=recent)
        collector_calls = []

        result = guarded_collect_wait_times(
            FakeEngine(connection),
            lambda: collector_calls.append(True),
            interval_seconds=300,
            now=self.now,
        )

        self.assertEqual("refresh_not_due", result["status"])
        self.assertEqual([], collector_calls)

    def test_stale_refresh_collects_and_persists_completion(self):
        old = self.now - timedelta(seconds=600)
        connection = FakeConnection(state_last_refresh=old, wait_last_refresh=old)
        collector_calls = []

        def collect():
            collector_calls.append(True)
            return {"inserted": 42}

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
        self.assertIsNotNone(connection.state_last_refresh)
        self.assertEqual("persistent-v2", result["refresh_guard"])

    def test_second_request_inside_window_does_not_collect_again(self):
        old = self.now - timedelta(seconds=600)
        connection = FakeConnection(state_last_refresh=old, wait_last_refresh=old)
        collector_calls = []

        def collect():
            collector_calls.append(True)
            return {"inserted": 17}

        first = guarded_collect_wait_times(
            FakeEngine(connection),
            collect,
            interval_seconds=300,
            now=self.now,
        )
        second = guarded_collect_wait_times(
            FakeEngine(connection),
            collect,
            interval_seconds=300,
            now=self.now + timedelta(seconds=60),
        )

        self.assertEqual("refreshed", first["status"])
        self.assertEqual("refresh_not_due", second["status"])
        self.assertEqual([True], collector_calls)


if __name__ == "__main__":
    unittest.main()

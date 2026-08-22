import unittest
from datetime import datetime
from types import SimpleNamespace

from ride_read import get_latest_rides


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeConnection:
    def __init__(self, table_exists=True, rows=None):
        self.table_exists = table_exists
        self.rows = list(rows or [])
        self.statements = []

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split()).lower()
        self.statements.append(sql)
        if "to_regclass('public.wait_times')" in sql:
            return ScalarResult("wait_times" if self.table_exists else None)
        if "select distinct on (park, ride_name)" in sql:
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


def include_ride(name):
    return not str(name).startswith("Skip")


class RideReadTests(unittest.TestCase):
    def test_missing_table_returns_empty_without_schema_or_collection_work(self):
        connection = FakeConnection(table_exists=False)
        result = get_latest_rides(FakeEngine(connection), include_ride)

        self.assertEqual([], result)
        self.assertEqual(1, len(connection.statements))
        self.assertNotIn("alter table", " ".join(connection.statements))
        self.assertNotIn("create table", " ".join(connection.statements))

    def test_latest_rows_are_mapped_and_non_rides_filtered(self):
        connection = FakeConnection(rows=[
            SimpleNamespace(
                park="Epcot",
                ride_name="Spaceship Earth",
                land="World Celebration",
                wait_time=10,
                is_open=True,
                created_at=datetime(2026, 8, 22, 17, 0, 0),
            ),
            SimpleNamespace(
                park="Epcot",
                ride_name="Skip Show",
                land="World Showcase",
                wait_time=0,
                is_open=True,
                created_at=datetime(2026, 8, 22, 17, 0, 0),
            ),
        ])

        result = get_latest_rides(FakeEngine(connection), include_ride)

        self.assertEqual(1, len(result))
        self.assertEqual("Spaceship Earth", result[0]["name"])
        self.assertEqual("2026-08-22T17:00:00", result[0]["created_at"])
        joined = " ".join(connection.statements)
        self.assertNotIn("alter table", joined)
        self.assertNotIn("create table", joined)
        self.assertNotIn("insert into", joined)


if __name__ == "__main__":
    unittest.main()

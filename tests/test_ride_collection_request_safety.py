from pathlib import Path

from ride_collection import collect_wait_times_without_schema


class FakeResult:
    def __init__(self, scalar_value=None):
        self.scalar_value = scalar_value

    def scalar(self):
        return self.scalar_value


class FakeConnection:
    def __init__(self):
        self.statements = []
        self.inserts = []
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=None):
        sql = str(statement)
        normalized = " ".join(sql.upper().split())
        self.statements.append(normalized)

        assert "CREATE TABLE" not in normalized
        assert "ALTER TABLE" not in normalized

        if "INSERT INTO WAIT_TIMES" in normalized:
            self.inserts.append(params)
            return FakeResult()
        if "SELECT COUNT(*) FROM WAIT_TIMES" in normalized:
            return FakeResult(len(self.inserts))
        return FakeResult()

    def commit(self):
        self.commits += 1


class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()

    def connect(self):
        return self.connection


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "lands": [
                {
                    "name": "World Celebration",
                    "rides": [
                        {
                            "name": "Spaceship Earth",
                            "wait_time": 15,
                            "is_open": True,
                        }
                    ],
                }
            ]
        }


def test_live_collector_never_runs_schema_ddl():
    engine = FakeEngine()

    result = collect_wait_times_without_schema(
        engine,
        [{"id": 5, "name": "Epcot"}],
        lambda name: False,
        lambda name: False,
        request_get=lambda url, timeout: FakeResponse(),
    )

    assert result["inserted"] == 1
    assert result["total_historical_entries"] == 1
    assert engine.connection.commits == 1
    assert len(engine.connection.inserts) == 1
    assert engine.connection.inserts[0]["park"] == "Epcot"


def test_production_refresh_route_uses_request_safe_collector():
    source = Path("app.py").read_text()

    assert "bootstrap_wait_times_schema()" in source
    assert "collect_wait_times_without_schema" in source
    assert "guarded_collect_wait_times(engine, _collect_wait_times_request_safe)" in source
    assert "guarded_collect_wait_times(engine, collect_wait_times)" not in source

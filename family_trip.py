import hmac
import json
import os
from datetime import datetime, timezone

from flask import jsonify, request
from sqlalchemy import text

FAMILY_TRIP_ID = "family"
FAMILY_KEY_HEADER = "X-CastleWatch-Key"
MAX_PAYLOAD_BYTES = 500_000
WRITE_LOCK_KEY = "castlewatch_family_trip"
HISTORY_LIMIT = 25


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def _json_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def setup_family_trip_database(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS family_trip_state (
            id TEXT PRIMARY KEY,
            payload JSONB NOT NULL,
            version INTEGER NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS family_trip_history (
            id TEXT NOT NULL,
            version INTEGER NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            restored_from_version INTEGER,
            PRIMARY KEY (id, version)
        )
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS family_trip_history_lookup
        ON family_trip_history (id, version DESC)
    """))
    connection.execute(text("""
        INSERT INTO family_trip_history (id, version, payload, created_at)
        SELECT id, version, payload, updated_at
        FROM family_trip_state
        WHERE id = :id
        ON CONFLICT (id, version) DO NOTHING
    """), {"id": FAMILY_TRIP_ID})


def _authorization_error():
    expected_key = os.getenv("CASTLEWATCH_FAMILY_KEY", "").strip()
    if not expected_key:
        return jsonify({
            "status": "not_configured",
            "message": "Shared family storage is disabled until CASTLEWATCH_FAMILY_KEY is configured.",
        }), 503

    provided_key = request.headers.get(FAMILY_KEY_HEADER, "")
    if not provided_key or not hmac.compare_digest(provided_key, expected_key):
        return jsonify({
            "status": "unauthorized",
            "message": "The CastleWatch family key is missing or incorrect.",
        }), 401

    return None


def _row_payload(row):
    if row is None:
        return {
            "status": "empty",
            "version": 0,
            "payload": None,
            "updatedAt": None,
        }

    payload = _json_value(row["payload"])
    updated_at = row["updated_at"]
    return {
        "status": "ok",
        "version": row["version"],
        "payload": payload,
        "updatedAt": updated_at.isoformat() if updated_at else None,
    }


def _history_summary(payload):
    payload = _json_value(payload) or {}
    reservations = payload.get("reservations")
    if not isinstance(reservations, list):
        reservations = []
    profile = payload.get("tripProfile")
    if not isinstance(profile, dict):
        profile = {}
    approval = payload.get("approval")
    if not isinstance(approval, dict):
        approval = {}

    return {
        "reservationCount": len(reservations),
        "tripName": profile.get("tripName") or "Family trip",
        "activeScenario": approval.get("activeScenario") or "base",
        "locked": bool(approval.get("locked")),
    }


def _history_entry(row, current_version):
    created_at = row["created_at"]
    return {
        "version": row["version"],
        "createdAt": created_at.isoformat() if created_at else None,
        "restoredFromVersion": row["restored_from_version"],
        "isCurrent": row["version"] == current_version,
        **_history_summary(row["payload"]),
    }


def _validate_payload(payload):
    if not isinstance(payload, dict):
        return None, (jsonify({
            "status": "invalid_request",
            "message": "payload must be a JSON object.",
        }), 400)

    serialized_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    payload_size = len(serialized_payload.encode("utf-8"))
    if payload_size > MAX_PAYLOAD_BYTES:
        return None, (jsonify({
            "status": "payload_too_large",
            "message": f"The shared trip payload exceeds the {MAX_PAYLOAD_BYTES}-byte limit.",
        }), 413)

    return serialized_payload, None


def _prune_history(connection):
    connection.execute(text("""
        DELETE FROM family_trip_history
        WHERE id = :id
          AND version NOT IN (
              SELECT version
              FROM family_trip_history
              WHERE id = :id
              ORDER BY version DESC
              LIMIT :history_limit
          )
    """), {
        "id": FAMILY_TRIP_ID,
        "history_limit": HISTORY_LIMIT,
    })


def _version_conflict_response(current):
    response = _row_payload(current)
    response.update({
        "status": "version_conflict",
        "message": "Shared trip data changed on another device. Download the current version before saving again.",
    })
    return jsonify(response), 409


def get_family_trip(engine):
    authorization_error = _authorization_error()
    if authorization_error:
        return authorization_error

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        row = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

    return jsonify(_row_payload(row))


def get_family_trip_history(engine):
    authorization_error = _authorization_error()
    if authorization_error:
        return authorization_error

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        current = connection.execute(text("""
            SELECT version
            FROM family_trip_state
            WHERE id = :id
        """), {"id": FAMILY_TRIP_ID}).mappings().first()
        current_version = current["version"] if current else 0
        rows = connection.execute(text("""
            SELECT version, payload, created_at, restored_from_version
            FROM family_trip_history
            WHERE id = :id
            ORDER BY version DESC
            LIMIT :history_limit
        """), {
            "id": FAMILY_TRIP_ID,
            "history_limit": HISTORY_LIMIT,
        }).mappings().all()

    return jsonify({
        "status": "ok",
        "currentVersion": current_version,
        "historyLimit": HISTORY_LIMIT,
        "entries": [_history_entry(row, current_version) for row in rows],
    })


def get_family_trip_history_version(engine, version):
    authorization_error = _authorization_error()
    if authorization_error:
        return authorization_error

    if not isinstance(version, int) or version < 1:
        return jsonify({
            "status": "invalid_request",
            "message": "History version must be a positive integer.",
        }), 400

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        row = connection.execute(text("""
            SELECT version, payload, created_at, restored_from_version
            FROM family_trip_history
            WHERE id = :id AND version = :version
        """), {
            "id": FAMILY_TRIP_ID,
            "version": version,
        }).mappings().first()

    if row is None:
        return jsonify({
            "status": "not_found",
            "message": f"Shared trip version {version} is no longer available.",
        }), 404

    created_at = row["created_at"]
    return jsonify({
        "status": "ok",
        "version": row["version"],
        "payload": _json_value(row["payload"]),
        "createdAt": created_at.isoformat() if created_at else None,
        "restoredFromVersion": row["restored_from_version"],
        "summary": _history_summary(row["payload"]),
    })


def put_family_trip(engine):
    authorization_error = _authorization_error()
    if authorization_error:
        return authorization_error

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({
            "status": "invalid_request",
            "message": "The request body must be a JSON object.",
        }), 400

    expected_version = body.get("expectedVersion")
    payload = body.get("payload")

    if not isinstance(expected_version, int) or expected_version < 0:
        return jsonify({
            "status": "invalid_request",
            "message": "expectedVersion must be a non-negative integer.",
        }), 400

    serialized_payload, payload_error = _validate_payload(payload)
    if payload_error:
        return payload_error

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        connection.execute(text("""
            SELECT pg_advisory_xact_lock(hashtext(:lock_key))
        """), {"lock_key": WRITE_LOCK_KEY})
        current = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
            FOR UPDATE
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

        current_version = current["version"] if current else 0
        if expected_version != current_version:
            return _version_conflict_response(current)

        next_version = current_version + 1
        if current is None:
            connection.execute(text("""
                INSERT INTO family_trip_state (id, payload, version, updated_at)
                VALUES (:id, CAST(:payload AS JSONB), :version, NOW())
            """), {
                "id": FAMILY_TRIP_ID,
                "payload": serialized_payload,
                "version": next_version,
            })
        else:
            connection.execute(text("""
                UPDATE family_trip_state
                SET payload = CAST(:payload AS JSONB),
                    version = :version,
                    updated_at = NOW()
                WHERE id = :id
            """), {
                "id": FAMILY_TRIP_ID,
                "payload": serialized_payload,
                "version": next_version,
            })

        connection.execute(text("""
            INSERT INTO family_trip_history (id, version, payload, created_at, restored_from_version)
            VALUES (:id, :version, CAST(:payload AS JSONB), NOW(), NULL)
            ON CONFLICT (id, version) DO NOTHING
        """), {
            "id": FAMILY_TRIP_ID,
            "version": next_version,
            "payload": serialized_payload,
        })
        _prune_history(connection)

        saved = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

    response = _row_payload(saved)
    response["savedAt"] = _utc_now_iso()
    return jsonify(response)


def restore_family_trip_version(engine):
    authorization_error = _authorization_error()
    if authorization_error:
        return authorization_error

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({
            "status": "invalid_request",
            "message": "The request body must be a JSON object.",
        }), 400

    expected_version = body.get("expectedVersion")
    source_version = body.get("sourceVersion")
    if not isinstance(expected_version, int) or expected_version < 1:
        return jsonify({
            "status": "invalid_request",
            "message": "expectedVersion must be a positive integer.",
        }), 400
    if not isinstance(source_version, int) or source_version < 1:
        return jsonify({
            "status": "invalid_request",
            "message": "sourceVersion must be a positive integer.",
        }), 400

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        connection.execute(text("""
            SELECT pg_advisory_xact_lock(hashtext(:lock_key))
        """), {"lock_key": WRITE_LOCK_KEY})
        current = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
            FOR UPDATE
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

        current_version = current["version"] if current else 0
        if expected_version != current_version:
            return _version_conflict_response(current)
        if source_version == current_version:
            return jsonify({
                "status": "invalid_request",
                "message": "The selected history version is already the current shared plan.",
            }), 400

        source = connection.execute(text("""
            SELECT payload
            FROM family_trip_history
            WHERE id = :id AND version = :version
        """), {
            "id": FAMILY_TRIP_ID,
            "version": source_version,
        }).mappings().first()
        if source is None:
            return jsonify({
                "status": "not_found",
                "message": f"Shared trip version {source_version} is no longer available.",
            }), 404

        source_payload = _json_value(source["payload"])
        serialized_payload, payload_error = _validate_payload(source_payload)
        if payload_error:
            return payload_error

        next_version = current_version + 1
        connection.execute(text("""
            UPDATE family_trip_state
            SET payload = CAST(:payload AS JSONB),
                version = :version,
                updated_at = NOW()
            WHERE id = :id
        """), {
            "id": FAMILY_TRIP_ID,
            "payload": serialized_payload,
            "version": next_version,
        })
        connection.execute(text("""
            INSERT INTO family_trip_history (id, version, payload, created_at, restored_from_version)
            VALUES (:id, :version, CAST(:payload AS JSONB), NOW(), :source_version)
        """), {
            "id": FAMILY_TRIP_ID,
            "version": next_version,
            "payload": serialized_payload,
            "source_version": source_version,
        })
        _prune_history(connection)

        saved = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

    response = _row_payload(saved)
    response.update({
        "savedAt": _utc_now_iso(),
        "restoredFromVersion": source_version,
    })
    return jsonify(response)

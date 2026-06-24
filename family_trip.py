import hmac
import json
import os
from datetime import datetime, timezone

from flask import jsonify, request
from sqlalchemy import text

FAMILY_TRIP_ID = "family"
FAMILY_KEY_HEADER = "X-CastleWatch-Key"
MAX_PAYLOAD_BYTES = 500_000


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def setup_family_trip_database(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS family_trip_state (
            id TEXT PRIMARY KEY,
            payload JSONB NOT NULL,
            version INTEGER NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))


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

    payload = row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    updated_at = row["updated_at"]
    return {
        "status": "ok",
        "version": row["version"],
        "payload": payload,
        "updatedAt": updated_at.isoformat() if updated_at else None,
    }


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

    if not isinstance(payload, dict):
        return jsonify({
            "status": "invalid_request",
            "message": "payload must be a JSON object.",
        }), 400

    serialized_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    payload_size = len(serialized_payload.encode("utf-8"))
    if payload_size > MAX_PAYLOAD_BYTES:
        return jsonify({
            "status": "payload_too_large",
            "message": f"The shared trip payload exceeds the {MAX_PAYLOAD_BYTES}-byte limit.",
        }), 413

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        current = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
            FOR UPDATE
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

        current_version = current["version"] if current else 0
        if expected_version != current_version:
            response = _row_payload(current)
            response.update({
                "status": "version_conflict",
                "message": "Shared trip data changed on another device. Download the current version before saving again.",
            })
            return jsonify(response), 409

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

        saved = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
        """), {"id": FAMILY_TRIP_ID}).mappings().first()

    response = _row_payload(saved)
    response["savedAt"] = _utc_now_iso()
    return jsonify(response)

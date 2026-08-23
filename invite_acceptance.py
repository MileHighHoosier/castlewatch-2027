from datetime import datetime, timezone

from flask import jsonify, request
from sqlalchemy import text

from accounts_access import _token_pepper
from accounts_auth import (
    DEVICE_TOKEN_KIND,
    INVITE_TOKEN_KIND,
    generate_access_token,
    hash_access_token,
    normalize_display_name,
    parse_access_token,
    safe_device_record,
    verify_access_token,
)
from accounts_schema import setup_accounts_database


def _error(status: str, message: str, code: int):
    return jsonify({"status": status, "message": message}), code


def _safe_device(row):
    record = safe_device_record(row)
    for key in ("createdAt", "lastSeenAt", "lastReadAt", "lastWriteAt", "revokedAt"):
        value = record.get(key)
        record[key] = value.isoformat() if hasattr(value, "isoformat") else value
    return record


def _prefix_for(token):
    parsed = parse_access_token(token)
    if parsed is None:
        raise ValueError("Generated token could not be parsed.")
    return parsed.lookup_prefix


def accept_family_invite_atomic(engine):
    """Consume an invite exactly once by locking the matching invite row first."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("invalid_request", "The request body must be a JSON object.", 400)

    invite_token = body.get("inviteToken")
    parsed = parse_access_token(invite_token, expected_kind=INVITE_TOKEN_KIND)
    if parsed is None:
        return _error("unauthorized", "The invite token is missing or incorrect.", 401)

    pepper = _token_pepper()
    if not pepper:
        return _error(
            "not_configured",
            "Device authorization is disabled until a token pepper or family key is configured.",
            503,
        )

    device_name = normalize_display_name(body.get("deviceName"), fallback="New device")
    device_token = generate_access_token(DEVICE_TOKEN_KIND)
    device_prefix = _prefix_for(device_token)
    device_hash = hash_access_token(device_token, pepper)

    with engine.begin() as connection:
        setup_accounts_database(connection)
        invite_rows = connection.execute(text("""
            SELECT
                id::text AS id,
                family_id,
                role,
                invite_hash,
                invite_prefix,
                label,
                status,
                expires_at,
                created_at,
                accepted_at
            FROM castlewatch_invites
            WHERE invite_prefix = :invite_prefix
            FOR UPDATE
        """), {"invite_prefix": parsed.lookup_prefix}).mappings().all()

        invite = None
        for row in invite_rows:
            if verify_access_token(
                invite_token,
                row["invite_hash"],
                pepper,
                expected_kind=INVITE_TOKEN_KIND,
            ):
                invite = row
                break

        if invite is None:
            return _error("unauthorized", "The invite token is missing or incorrect.", 401)

        if invite["status"] != "open":
            return _error("already_used", "This invite has already been used or is no longer active.", 409)

        expires_at = invite["expires_at"]
        if expires_at and expires_at < datetime.now(timezone.utc):
            connection.execute(text("""
                UPDATE castlewatch_invites
                SET status = 'expired'
                WHERE id = CAST(:invite_id AS UUID)
                  AND status = 'open'
            """), {"invite_id": invite["id"]})
            return _error("expired", "This invite has expired.", 410)

        device = connection.execute(text("""
            INSERT INTO castlewatch_devices (
                family_id,
                member_id,
                display_name,
                token_hash,
                token_prefix,
                role,
                last_seen_at
            )
            VALUES (
                :family_id,
                NULL,
                :display_name,
                :token_hash,
                :token_prefix,
                :role,
                NOW()
            )
            RETURNING
                id::text AS id,
                display_name,
                role,
                status,
                token_prefix,
                created_at,
                last_seen_at,
                last_read_at,
                last_write_at,
                revoked_at
        """), {
            "family_id": invite["family_id"],
            "display_name": device_name,
            "token_hash": device_hash,
            "token_prefix": device_prefix,
            "role": invite["role"],
        }).mappings().first()

        consumed = connection.execute(text("""
            UPDATE castlewatch_invites
            SET status = 'accepted',
                accepted_at = NOW(),
                accepted_device_id = CAST(:device_id AS UUID)
            WHERE id = CAST(:invite_id AS UUID)
              AND status = 'open'
            RETURNING id::text AS id
        """), {
            "device_id": device["id"],
            "invite_id": invite["id"],
        }).mappings().first()

        if consumed is None:
            raise RuntimeError("Invite acceptance lost its locked open state.")

    return jsonify({
        "status": "ok",
        "deviceToken": device_token,
        "device": _safe_device(device),
    })

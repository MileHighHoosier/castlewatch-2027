from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from sqlalchemy import text

from accounts_access import _token_pepper, authorize_request
from accounts_auth import (
    DEVICE_TOKEN_KIND,
    INVITE_TOKEN_KIND,
    generate_access_token,
    hash_access_token,
    normalize_display_name,
    normalize_role,
    parse_access_token,
    safe_device_record,
    safe_invite_record,
    verify_access_token,
)
from accounts_schema import setup_accounts_database

INVITE_EXPIRATION_DAYS = 7


def _json_body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else None


def _error(status: str, message: str, code: int):
    return jsonify({"status": status, "message": message}), code


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _safe_device(row):
    record = safe_device_record(row)
    for key in ("createdAt", "lastSeenAt", "lastReadAt", "lastWriteAt", "revokedAt"):
        record[key] = _iso(record.get(key))
    return record


def _safe_invite(row):
    record = safe_invite_record(row)
    for key in ("expiresAt", "createdAt", "acceptedAt"):
        record[key] = _iso(record.get(key))
    return record


def _prefix_for(token):
    parsed = parse_access_token(token)
    if parsed is None:
        raise ValueError("Generated token could not be parsed.")
    return parsed.lookup_prefix


def list_family_devices(engine):
    with engine.begin() as connection:
        setup_accounts_database(connection)
        authorization = authorize_request(connection, permission="manage")
        if authorization.error:
            return authorization.error
        rows = connection.execute(text("""
            SELECT
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
            FROM castlewatch_devices
            WHERE family_id = :family_id
            ORDER BY created_at DESC
        """), {"family_id": authorization.actor.family_id}).mappings().all()

    return jsonify({
        "status": "ok",
        "devices": [_safe_device(row) for row in rows],
    })


def create_family_invite(engine):
    body = _json_body()
    if body is None:
        return _error("invalid_request", "The request body must be a JSON object.", 400)

    role = normalize_role(body.get("role") or "editor")
    if role not in {"editor", "viewer"}:
        return _error("invalid_request", "Invite role must be editor or viewer.", 400)

    label = normalize_display_name(body.get("label"), fallback="New device")
    invite_token = generate_access_token(INVITE_TOKEN_KIND)
    invite_prefix = _prefix_for(invite_token)
    pepper = _token_pepper()
    if not pepper:
        return _error("not_configured", "Device authorization is disabled until a token pepper or family key is configured.", 503)
    invite_hash = hash_access_token(invite_token, pepper)
    expires_at = datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRATION_DAYS)

    with engine.begin() as connection:
        setup_accounts_database(connection)
        authorization = authorize_request(connection, permission="manage")
        if authorization.error:
            return authorization.error
        row = connection.execute(text("""
            INSERT INTO castlewatch_invites (
                family_id,
                created_by_member_id,
                role,
                invite_hash,
                invite_prefix,
                label,
                expires_at
            )
            VALUES (
                :family_id,
                CAST(:created_by_member_id AS UUID),
                :role,
                :invite_hash,
                :invite_prefix,
                :label,
                :expires_at
            )
            RETURNING
                id::text AS id,
                role,
                status,
                invite_prefix,
                label,
                expires_at,
                created_at,
                accepted_at
        """), {
            "family_id": authorization.actor.family_id,
            "created_by_member_id": authorization.actor.member_id,
            "role": role,
            "invite_hash": invite_hash,
            "invite_prefix": invite_prefix,
            "label": label,
            "expires_at": expires_at,
        }).mappings().first()

    return jsonify({
        "status": "ok",
        "inviteToken": invite_token,
        "invite": _safe_invite(row),
    })


def accept_family_invite(engine):
    body = _json_body()
    if body is None:
        return _error("invalid_request", "The request body must be a JSON object.", 400)

    invite_token = body.get("inviteToken")
    parsed = parse_access_token(invite_token, expected_kind=INVITE_TOKEN_KIND)
    if parsed is None:
        return _error("unauthorized", "The invite token is missing or incorrect.", 401)

    pepper = _token_pepper()
    if not pepper:
        return _error("not_configured", "Device authorization is disabled until a token pepper or family key is configured.", 503)

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
              AND status = 'open'
        """), {"invite_prefix": parsed.lookup_prefix}).mappings().all()

        invite = None
        for row in invite_rows:
            if verify_access_token(invite_token, row["invite_hash"], pepper, expected_kind=INVITE_TOKEN_KIND):
                invite = row
                break

        if invite is None:
            return _error("unauthorized", "The invite token is missing or incorrect.", 401)

        expires_at = invite["expires_at"]
        if expires_at and expires_at < datetime.now(timezone.utc):
            connection.execute(text("""
                UPDATE castlewatch_invites
                SET status = 'expired'
                WHERE id = CAST(:invite_id AS UUID)
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

        connection.execute(text("""
            UPDATE castlewatch_invites
            SET status = 'accepted',
                accepted_at = NOW(),
                accepted_device_id = CAST(:device_id AS UUID)
            WHERE id = CAST(:invite_id AS UUID)
        """), {
            "device_id": device["id"],
            "invite_id": invite["id"],
        })

    return jsonify({
        "status": "ok",
        "deviceToken": device_token,
        "device": _safe_device(device),
    })


def rename_family_device(engine):
    body = _json_body()
    if body is None:
        return _error("invalid_request", "The request body must be a JSON object.", 400)
    device_id = body.get("deviceId")
    if not isinstance(device_id, str) or not device_id:
        return _error("invalid_request", "deviceId is required.", 400)
    display_name = normalize_display_name(body.get("displayName"))

    with engine.begin() as connection:
        setup_accounts_database(connection)
        authorization = authorize_request(connection, permission="read")
        if authorization.error:
            return authorization.error
        actor = authorization.actor
        if actor.role != "owner" and actor.device_id != device_id:
            return _error("forbidden", "Only an owner or the current device can rename this device.", 403)

        row = connection.execute(text("""
            UPDATE castlewatch_devices
            SET display_name = :display_name
            WHERE id = CAST(:device_id AS UUID)
              AND family_id = :family_id
              AND status = 'active'
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
            "display_name": display_name,
            "device_id": device_id,
            "family_id": actor.family_id,
        }).mappings().first()

    if row is None:
        return _error("not_found", "The requested device was not found.", 404)
    return jsonify({"status": "ok", "device": _safe_device(row)})


def revoke_family_device(engine):
    body = _json_body()
    if body is None:
        return _error("invalid_request", "The request body must be a JSON object.", 400)
    device_id = body.get("deviceId")
    if not isinstance(device_id, str) or not device_id:
        return _error("invalid_request", "deviceId is required.", 400)

    with engine.begin() as connection:
        setup_accounts_database(connection)
        authorization = authorize_request(connection, permission="manage")
        if authorization.error:
            return authorization.error
        actor = authorization.actor
        if actor.device_id and actor.device_id == device_id:
            return _error("invalid_request", "The current device cannot revoke itself.", 400)

        row = connection.execute(text("""
            UPDATE castlewatch_devices
            SET status = 'revoked',
                revoked_at = NOW()
            WHERE id = CAST(:device_id AS UUID)
              AND family_id = :family_id
              AND status = 'active'
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
            "device_id": device_id,
            "family_id": actor.family_id,
        }).mappings().first()

    if row is None:
        return _error("not_found", "The requested device was not found.", 404)
    return jsonify({"status": "ok", "device": _safe_device(row)})

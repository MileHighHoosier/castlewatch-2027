from datetime import datetime, timedelta, timezone

from flask import jsonify, request
from sqlalchemy import text

from accounts_access import (
    DEVICE_TOKEN_HEADER,
    FAMILY_KEY_HEADER,
    matching_access_token_pepper,
    authorize_request,
    preauthorize_legacy_request,
    token_pepper_for_new_credentials,
)
from accounts_auth import (
    DEVICE_TOKEN_KIND,
    INVITE_TOKEN_KIND,
    can_manage_devices,
    can_write_shared_plan,
    generate_access_token,
    hash_access_token,
    normalize_display_name,
    normalize_role,
    parse_access_token,
    safe_device_record,
    safe_invite_record,
)
from accounts_schema import (
    DEFAULT_OWNER_MEMBER_ID,
    FAMILY_WORKSPACE_ID,
    setup_accounts_database,
)

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


def _device_by_id(connection, family_id, device_id):
    if not device_id:
        return None
    return connection.execute(text("""
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
          AND id = CAST(:device_id AS UUID)
    """), {
        "family_id": family_id,
        "device_id": device_id,
    }).mappings().first()


def _verified_current_device_token_record(connection):
    token = request.headers.get(DEVICE_TOKEN_HEADER, "").strip()
    parsed = parse_access_token(token, expected_kind=DEVICE_TOKEN_KIND)
    if parsed is None:
        return None

    rows = connection.execute(text("""
        SELECT
            id::text AS id,
            family_id,
            display_name,
            role,
            status,
            token_hash,
            token_prefix,
            created_at,
            last_seen_at,
            last_read_at,
            last_write_at,
            revoked_at
        FROM castlewatch_devices
        WHERE token_prefix = :token_prefix
    """), {"token_prefix": parsed.lookup_prefix}).mappings().all()

    for row in rows:
        if matching_access_token_pepper(
            token,
            row["token_hash"],
            expected_kind=DEVICE_TOKEN_KIND,
        ):
            return row
    return None


def check_family_device_access(engine):
    with engine.begin() as connection:
        setup_accounts_database(connection)
        authorization = authorize_request(connection, permission="read")
        if authorization.error:
            device = _verified_current_device_token_record(connection)
            if device and device.get("status") == "revoked":
                return jsonify({
                    "status": "revoked",
                    "authState": "revoked_device_token",
                    "message": "This saved device token was revoked. Reconnect with a new invite or use the family key.",
                    "device": _safe_device(device),
                    "canManageDevices": False,
                    "canWriteSharedPlan": False,
                    "migrationRecommended": False,
                }), 401
            return authorization.error

        actor = authorization.actor
        if actor.auth_type == "legacy_key":
            return jsonify({
                "status": "ok",
                "authState": "family_key",
                "role": "owner",
                "device": None,
                "canManageDevices": True,
                "canWriteSharedPlan": True,
                "migrationRecommended": True,
                "message": "This browser is using the family key owner path. Keep it enabled for recovery until device access is fully verified.",
            })

        device = _device_by_id(connection, actor.family_id, actor.device_id)
        return jsonify({
            "status": "ok",
            "authState": "device_token",
            "role": actor.role,
            "device": _safe_device(device) if device else None,
            "canManageDevices": can_manage_devices(actor.role),
            "canWriteSharedPlan": can_write_shared_plan(actor.role),
            "migrationRecommended": False,
            "message": "This browser is connected with a device token.",
        })


def bootstrap_family_owner_device(engine):
    """Create the first owner device through the explicit family-key recovery path."""
    body = _json_body()
    if body is None:
        return _error("invalid_request", "The request body must be a JSON object.", 400)

    if request.headers.get(DEVICE_TOKEN_HEADER, "").strip():
        if not request.headers.get(FAMILY_KEY_HEADER, ""):
            return _error(
                "unauthorized",
                "Owner bootstrap requires the CastleWatch family key.",
                401,
            )
        return _error(
            "invalid_request",
            "Owner bootstrap accepts the family key only, not multiple credentials.",
            400,
        )

    device_name = normalize_display_name(body.get("deviceName"), fallback="Owner device")
    pepper = token_pepper_for_new_credentials()
    if not pepper:
        return _error(
            "not_configured",
            "Device authorization is disabled until a token pepper or family key is configured.",
            503,
        )

    with engine.begin() as connection:
        setup_accounts_database(connection)
        preauthorization = preauthorize_legacy_request(permission="manage")
        authorization = authorize_request(
            connection,
            permission="manage",
            preauthorization=preauthorization,
        )
        if authorization.error:
            return authorization.error

        owner_member = connection.execute(text("""
            SELECT
                id::text AS id,
                family_id,
                role,
                status
            FROM castlewatch_members
            WHERE id = CAST(:member_id AS UUID)
              AND family_id = :family_id
              AND role = 'owner'
              AND status = 'active'
            FOR UPDATE
        """), {
            "member_id": DEFAULT_OWNER_MEMBER_ID,
            "family_id": FAMILY_WORKSPACE_ID,
        }).mappings().first()
        if owner_member is None:
            return _error(
                "bootstrap_unavailable",
                "The seeded family owner is unavailable for device bootstrap.",
                409,
            )

        existing_owner = connection.execute(text("""
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
              AND role = 'owner'
              AND status = 'active'
            ORDER BY created_at ASC
            LIMIT 1
        """), {"family_id": FAMILY_WORKSPACE_ID}).mappings().first()
        if existing_owner is not None:
            return jsonify({
                "status": "owner_device_exists",
                "message": "An active owner device already exists. Revoke it through the family-key recovery path before bootstrapping a replacement.",
                "device": _safe_device(existing_owner),
            }), 409

        device_token = generate_access_token(DEVICE_TOKEN_KIND)
        device_prefix = _prefix_for(device_token)
        device_hash = hash_access_token(device_token, pepper)
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
                CAST(:member_id AS UUID),
                :display_name,
                :token_hash,
                :token_prefix,
                'owner',
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
            "family_id": FAMILY_WORKSPACE_ID,
            "member_id": owner_member["id"],
            "display_name": device_name,
            "token_hash": device_hash,
            "token_prefix": device_prefix,
        }).mappings().first()

    response = jsonify({
        "status": "ok",
        "deviceToken": device_token,
        "device": _safe_device(device),
    })
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


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
    pepper = token_pepper_for_new_credentials()
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

    pepper = token_pepper_for_new_credentials()
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
            if matching_access_token_pepper(
                invite_token,
                row["invite_hash"],
                expected_kind=INVITE_TOKEN_KIND,
            ):
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

    response = jsonify({
        "status": "ok",
        "deviceToken": device_token,
        "device": _safe_device(device),
    })
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


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

        connection.execute(text("""
            SELECT id
            FROM castlewatch_members
            WHERE id = CAST(:member_id AS UUID)
              AND family_id = :family_id
              AND role = 'owner'
            FOR UPDATE
        """), {
            "member_id": DEFAULT_OWNER_MEMBER_ID,
            "family_id": actor.family_id,
        })

        target = connection.execute(text("""
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
            WHERE id = CAST(:device_id AS UUID)
              AND family_id = :family_id
              AND status = 'active'
            FOR UPDATE
        """), {
            "device_id": device_id,
            "family_id": actor.family_id,
        }).mappings().first()
        if target is None:
            return _error("not_found", "The requested device was not found.", 404)
        if target["role"] == "owner" and actor.auth_type != "legacy_key":
            return _error(
                "owner_recovery_required",
                "An owner device can be revoked only through the explicit family-key recovery path.",
                409,
            )

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

    payload = {"status": "ok", "device": _safe_device(row)}
    if row["role"] == "owner":
        payload.update({
            "recoveryRequired": True,
            "message": "The owner device was revoked through family-key recovery. Bootstrap a replacement owner device before relying on device-only access.",
        })
    return jsonify(payload)

import hmac
import os
from dataclasses import dataclass
from typing import Any

from flask import jsonify, request
from sqlalchemy import text

from accounts_auth import (
    DEVICE_TOKEN_KIND,
    can_manage_devices,
    can_read_shared_plan,
    can_view_operations,
    can_write_shared_plan,
    hash_access_token,
    parse_access_token,
    verify_access_token,
)
from accounts_schema import FAMILY_WORKSPACE_ID

FAMILY_KEY_HEADER = "X-CastleWatch-Key"
DEVICE_TOKEN_HEADER = "X-CastleWatch-Device-Token"
_PREAUTHORIZATION_UNSET = object()


@dataclass(frozen=True)
class AccessActor:
    family_id: str
    role: str
    auth_type: str
    member_id: str | None = None
    device_id: str | None = None


@dataclass(frozen=True)
class AuthorizationResult:
    actor: AccessActor | None = None
    error: Any | None = None


def _authorization_error(status: str, message: str, code: int):
    return AuthorizationResult(error=(jsonify({
        "status": status,
        "message": message,
    }), code))


def _expected_family_key() -> str:
    return os.getenv("CASTLEWATCH_FAMILY_KEY", "").strip()


def token_pepper_for_new_credentials() -> str:
    return (
        os.getenv("CASTLEWATCH_DEVICE_TOKEN_PEPPER", "").strip()
        or _expected_family_key()
    )


def token_peppers_for_verification() -> tuple[str, ...]:
    """Return current and transition peppers without exposing them to callers."""
    candidates = (
        token_pepper_for_new_credentials(),
        os.getenv("CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER", "").strip(),
        _expected_family_key(),
    )
    peppers = []
    for candidate in candidates:
        if candidate and candidate not in peppers:
            peppers.append(candidate)
    return tuple(peppers)


def matching_access_token_pepper(token, stored_hash, expected_kind):
    for pepper in token_peppers_for_verification():
        if verify_access_token(token, stored_hash, pepper, expected_kind=expected_kind):
            return pepper
    return None


def _token_pepper() -> str:
    """Backward-compatible private alias for the new-credential pepper."""
    return token_pepper_for_new_credentials()


def _permission_allowed(role: str, permission: str) -> bool:
    if permission == "read":
        return can_read_shared_plan(role)
    if permission == "write":
        return can_write_shared_plan(role)
    if permission == "manage":
        return can_manage_devices(role)
    if permission == "operations":
        return can_view_operations(role)
    return False


def _permission_error(permission: str):
    return _authorization_error(
        "forbidden",
        f"This device is not allowed to perform the requested {permission} action.",
        403,
    )


def _authorize_legacy_actor(connection, authorization: AuthorizationResult) -> AuthorizationResult:
    actor = authorization.actor
    if actor is None or actor.auth_type != "legacy_key":
        return authorization

    family = connection.execute(text("""
        SELECT legacy_family_key_enabled
        FROM castlewatch_families
        WHERE id = :family_id
    """), {"family_id": actor.family_id}).mappings().first()
    if family is None:
        return _authorization_error(
            "not_configured",
            "Family-key authorization is unavailable for this workspace.",
            503,
        )
    if not family.get("legacy_family_key_enabled"):
        return _authorization_error(
            "legacy_key_disabled",
            "Family-key recovery is disabled for this workspace. Use an active owner device or restore the recovery flag through the documented rollback procedure.",
            403,
        )
    return authorization


def preauthorize_legacy_request(permission: str = "read") -> AuthorizationResult | None:
    expected_key = _expected_family_key()
    provided_key = request.headers.get(FAMILY_KEY_HEADER, "").strip()
    provided_device_token = request.headers.get(DEVICE_TOKEN_HEADER, "").strip()

    if provided_key and provided_device_token:
        return _authorization_error(
            "invalid_request",
            "Select exactly one CastleWatch credential per request.",
            400,
        )

    if provided_key:
        if not expected_key:
            return _authorization_error(
                "not_configured",
                "Shared family storage is disabled until CASTLEWATCH_FAMILY_KEY is configured.",
                503,
            )
        if not hmac.compare_digest(provided_key, expected_key):
            return _authorization_error(
                "unauthorized",
                "The CastleWatch family key is missing or incorrect.",
                401,
            )
        actor = AccessActor(family_id=FAMILY_WORKSPACE_ID, role="owner", auth_type="legacy_key")
        if not _permission_allowed(actor.role, permission):
            return _permission_error(permission)
        return AuthorizationResult(actor=actor)

    if not provided_device_token:
        if not expected_key:
            return _authorization_error(
                "not_configured",
                "Shared family storage is disabled until CASTLEWATCH_FAMILY_KEY is configured.",
                503,
            )
        return _authorization_error(
            "unauthorized",
            "The CastleWatch family key or device token is missing or incorrect.",
            401,
        )

    return None


def authorize_device_request(connection, permission: str = "read") -> AuthorizationResult:
    token = request.headers.get(DEVICE_TOKEN_HEADER, "").strip()
    parsed = parse_access_token(token, expected_kind=DEVICE_TOKEN_KIND)
    if parsed is None:
        return _authorization_error(
            "unauthorized",
            "The CastleWatch device token is missing or incorrect.",
            401,
        )

    verification_peppers = token_peppers_for_verification()
    if not verification_peppers:
        return _authorization_error(
            "not_configured",
            "Device authorization is disabled until a token pepper or family key is configured.",
            503,
        )

    rows = connection.execute(text("""
        SELECT
            d.id::text AS id,
            d.family_id,
            d.member_id::text AS member_id,
            d.role,
            d.status,
            d.token_hash,
            d.token_prefix,
            m.status AS member_status
        FROM castlewatch_devices d
        LEFT JOIN castlewatch_members m ON d.member_id = m.id
        WHERE d.token_prefix = :token_prefix
          AND d.status = 'active'
    """), {"token_prefix": parsed.lookup_prefix}).mappings().all()

    actor = None
    matched_pepper = None
    for row in rows:
        member_status = row.get("member_status")
        if member_status is not None and member_status != "active":
            continue
        candidate_pepper = matching_access_token_pepper(
            token,
            row["token_hash"],
            expected_kind=DEVICE_TOKEN_KIND,
        )
        if candidate_pepper:
            actor = AccessActor(
                family_id=row["family_id"],
                role=row["role"],
                auth_type="device_token",
                member_id=row.get("member_id"),
                device_id=row["id"],
            )
            matched_pepper = candidate_pepper
            break

    if actor is None:
        return _authorization_error(
            "unauthorized",
            "The CastleWatch device token is missing or incorrect.",
            401,
        )

    if not _permission_allowed(actor.role, permission):
        return _permission_error(permission)

    timestamp_columns = ["last_seen_at"]
    if permission == "read":
        timestamp_columns.append("last_read_at")
    elif permission == "write":
        timestamp_columns.append("last_write_at")

    set_values = [f"{column} = NOW()" for column in timestamp_columns]
    update_parameters = {"device_id": actor.device_id}
    primary_pepper = token_pepper_for_new_credentials()
    if primary_pepper and matched_pepper != primary_pepper:
        set_values.append("token_hash = :token_hash")
        update_parameters["token_hash"] = hash_access_token(token, primary_pepper)

    set_clause = ", ".join(set_values)
    connection.execute(text(f"""
        UPDATE castlewatch_devices
        SET {set_clause}
        WHERE id = CAST(:device_id AS UUID)
    """), update_parameters)

    return AuthorizationResult(actor=actor)


def authorize_request(
    connection,
    permission: str = "read",
    preauthorization=_PREAUTHORIZATION_UNSET,
) -> AuthorizationResult:
    authorization = (
        preauthorize_legacy_request(permission)
        if preauthorization is _PREAUTHORIZATION_UNSET
        else preauthorization
    )
    if authorization is None:
        return authorize_device_request(connection, permission)
    if authorization.error:
        return authorization
    return _authorize_legacy_actor(connection, authorization)

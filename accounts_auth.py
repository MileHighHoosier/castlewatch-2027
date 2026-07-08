import base64
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

DEVICE_TOKEN_KIND = "device"
INVITE_TOKEN_KIND = "invite"
DEVICE_TOKEN_PREFIX = "cwdev"
INVITE_TOKEN_PREFIX = "cwinv"
TOKEN_PREFIX_BYTES = 6
TOKEN_SECRET_BYTES = 32
TOKEN_LOOKUP_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,24}$")
TOKEN_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{24,}$")
VALID_ROLES = {"owner", "editor", "viewer"}
WRITER_ROLES = {"owner", "editor"}
MANAGER_ROLES = {"owner"}
OPERATIONS_ROLES = {"owner", "editor"}


@dataclass(frozen=True)
class ParsedAccessToken:
    kind: str
    lookup_prefix: str
    raw_token: str


def _urlsafe_random(byte_count: int) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(byte_count)).decode("ascii").rstrip("=")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_role(role: Any) -> str | None:
    if not isinstance(role, str):
        return None
    normalized = role.strip().lower()
    return normalized if normalized in VALID_ROLES else None


def normalize_display_name(value: Any, fallback: str = "Unnamed device") -> str:
    if not isinstance(value, str):
        return fallback
    collapsed = " ".join(value.split())
    if not collapsed:
        return fallback
    return collapsed[:80]


def token_kind_prefix(kind: str) -> str:
    if kind == DEVICE_TOKEN_KIND:
        return DEVICE_TOKEN_PREFIX
    if kind == INVITE_TOKEN_KIND:
        return INVITE_TOKEN_PREFIX
    raise ValueError("Unsupported token kind.")


def generate_access_token(kind: str) -> str:
    public_prefix = token_kind_prefix(kind)
    lookup_prefix = _urlsafe_random(TOKEN_PREFIX_BYTES)
    secret = _urlsafe_random(TOKEN_SECRET_BYTES)
    return f"{public_prefix}_{lookup_prefix}_{secret}"


def parse_access_token(token: Any, expected_kind: str | None = None) -> ParsedAccessToken | None:
    if not isinstance(token, str):
        return None
    parts = token.strip().split("_")
    if len(parts) != 3:
        return None

    public_prefix, lookup_prefix, secret = parts
    if public_prefix == DEVICE_TOKEN_PREFIX:
        kind = DEVICE_TOKEN_KIND
    elif public_prefix == INVITE_TOKEN_PREFIX:
        kind = INVITE_TOKEN_KIND
    else:
        return None

    if expected_kind is not None and kind != expected_kind:
        return None
    if not TOKEN_LOOKUP_PATTERN.fullmatch(lookup_prefix):
        return None
    if not TOKEN_SECRET_PATTERN.fullmatch(secret):
        return None

    return ParsedAccessToken(kind=kind, lookup_prefix=lookup_prefix, raw_token=token.strip())


def hash_access_token(token: str, pepper: str) -> str:
    if not isinstance(pepper, str) or not pepper:
        raise ValueError("A non-empty token pepper is required.")
    parsed = parse_access_token(token)
    if parsed is None:
        raise ValueError("Cannot hash an invalid access token.")
    digest = hmac.new(
        pepper.encode("utf-8"),
        parsed.raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256:{digest}"


def verify_access_token(token: Any, stored_hash: Any, pepper: str, expected_kind: str | None = None) -> bool:
    if not isinstance(stored_hash, str) or not stored_hash.startswith("sha256:"):
        return False
    parsed = parse_access_token(token, expected_kind=expected_kind)
    if parsed is None:
        return False
    try:
        candidate_hash = hash_access_token(parsed.raw_token, pepper)
    except ValueError:
        return False
    return hmac.compare_digest(candidate_hash, stored_hash)


def redact_access_token(token: Any) -> str:
    parsed = parse_access_token(token)
    if parsed is None:
        return "invalid-token"
    return f"{token_kind_prefix(parsed.kind)}_{parsed.lookup_prefix}_…"


def can_read_shared_plan(role: Any) -> bool:
    return normalize_role(role) in VALID_ROLES


def can_write_shared_plan(role: Any) -> bool:
    return normalize_role(role) in WRITER_ROLES


def can_manage_devices(role: Any) -> bool:
    return normalize_role(role) in MANAGER_ROLES


def can_view_operations(role: Any) -> bool:
    return normalize_role(role) in OPERATIONS_ROLES


def safe_device_record(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id", "")),
        "displayName": normalize_display_name(row.get("display_name")),
        "role": normalize_role(row.get("role")) or "viewer",
        "status": str(row.get("status") or "unknown"),
        "tokenPrefix": str(row.get("token_prefix") or ""),
        "createdAt": row.get("created_at"),
        "lastSeenAt": row.get("last_seen_at"),
        "lastReadAt": row.get("last_read_at"),
        "lastWriteAt": row.get("last_write_at"),
        "revokedAt": row.get("revoked_at"),
    }


def safe_invite_record(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id", "")),
        "role": normalize_role(row.get("role")) or "viewer",
        "status": str(row.get("status") or "unknown"),
        "invitePrefix": str(row.get("invite_prefix") or ""),
        "label": normalize_display_name(row.get("label"), fallback="Invite"),
        "expiresAt": row.get("expires_at"),
        "createdAt": row.get("created_at"),
        "acceptedAt": row.get("accepted_at"),
    }

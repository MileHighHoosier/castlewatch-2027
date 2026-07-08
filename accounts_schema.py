from sqlalchemy import text

FAMILY_WORKSPACE_ID = "family"
DEFAULT_FAMILY_DISPLAY_NAME = "CastleWatch family"
DEFAULT_OWNER_MEMBER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_OWNER_DISPLAY_NAME = "Family owner"


def setup_accounts_database(connection):
    """Create additive account/device tables without changing legacy family sync."""
    connection.execute(text("""
        CREATE EXTENSION IF NOT EXISTS pgcrypto
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS castlewatch_families (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            legacy_family_key_enabled BOOLEAN NOT NULL DEFAULT TRUE
        )
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS castlewatch_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            family_id TEXT NOT NULL REFERENCES castlewatch_families(id) ON DELETE CASCADE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
            status TEXT NOT NULL CHECK (status IN ('active', 'disabled')) DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS castlewatch_members_family_lookup
        ON castlewatch_members (family_id, status, role)
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS castlewatch_devices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            family_id TEXT NOT NULL REFERENCES castlewatch_families(id) ON DELETE CASCADE,
            member_id UUID REFERENCES castlewatch_members(id) ON DELETE SET NULL,
            display_name TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            token_prefix TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
            status TEXT NOT NULL CHECK (status IN ('active', 'revoked')) DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ,
            last_read_at TIMESTAMPTZ,
            last_write_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ
        )
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS castlewatch_devices_family_lookup
        ON castlewatch_devices (family_id, status, last_seen_at DESC)
    """))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS castlewatch_invites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            family_id TEXT NOT NULL REFERENCES castlewatch_families(id) ON DELETE CASCADE,
            created_by_member_id UUID REFERENCES castlewatch_members(id) ON DELETE SET NULL,
            role TEXT NOT NULL CHECK (role IN ('editor', 'viewer')),
            invite_hash TEXT NOT NULL UNIQUE,
            invite_prefix TEXT NOT NULL,
            label TEXT,
            status TEXT NOT NULL CHECK (status IN ('open', 'accepted', 'revoked', 'expired')) DEFAULT 'open',
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            accepted_at TIMESTAMPTZ,
            accepted_device_id UUID REFERENCES castlewatch_devices(id) ON DELETE SET NULL
        )
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS castlewatch_invites_family_lookup
        ON castlewatch_invites (family_id, status, expires_at DESC)
    """))
    connection.execute(text("""
        INSERT INTO castlewatch_families (id, display_name)
        VALUES (:family_id, :display_name)
        ON CONFLICT (id) DO NOTHING
    """), {
        "family_id": FAMILY_WORKSPACE_ID,
        "display_name": DEFAULT_FAMILY_DISPLAY_NAME,
    })
    connection.execute(text("""
        INSERT INTO castlewatch_members (id, family_id, display_name, role, status)
        VALUES (:member_id, :family_id, :display_name, 'owner', 'active')
        ON CONFLICT (id) DO NOTHING
    """), {
        "member_id": DEFAULT_OWNER_MEMBER_ID,
        "family_id": FAMILY_WORKSPACE_ID,
        "display_name": DEFAULT_OWNER_DISPLAY_NAME,
    })

# Accounts, invitations and device management design

## Status

Design proposal only. This document does not add a production schema migration, new endpoint, or GUI change.

## Goals

- Replace the long-lived shared family key with named family members and revocable devices.
- Preserve the existing `CASTLEWATCH_FAMILY_KEY` workflow while the new model is introduced.
- Allow the owner to identify connected devices such as `Ryan iPhone`, `Katie iPhone`, or `home laptop`.
- Support invite-style onboarding without exposing raw keys or tokens in logs or the GUI.
- Prepare for simple roles: `owner`, `editor`, and `viewer`.
- Keep usage low by updating device heartbeat fields only when a read or write already occurs.

## Non-goals for the first implementation

- No public self-signup.
- No password login.
- No social login.
- No SMS delivery.
- No removal of the current family key.
- No production migration until the plan is reviewed.

## Current state to preserve

The current family sync API uses one environment-level family key from `CASTLEWATCH_FAMILY_KEY`. Requests send it in `X-CastleWatch-Key`. Authorized requests read and write one shared family document identified by the fixed `family` id. Writes require an `expectedVersion`, create a new shared version, insert a history snapshot, and prune history to the 25 most recent versions.

This behavior must continue to work throughout the migration.

## Proposed tables

### `castlewatch_families`

One row per shared family workspace.

```sql
CREATE TABLE castlewatch_families (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    legacy_family_key_enabled BOOLEAN NOT NULL DEFAULT TRUE
);
```

Initial seed: one family row with id `family`.

### `castlewatch_members`

People who can access a family workspace.

```sql
CREATE TABLE castlewatch_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id TEXT NOT NULL REFERENCES castlewatch_families(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    status TEXT NOT NULL CHECK (status IN ('active', 'disabled')) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX castlewatch_members_family_lookup
ON castlewatch_members (family_id, status, role);
```

First implementation can seed one owner member named `Family owner` when the new tables are created.

### `castlewatch_devices`

Each browser or phone that has been connected through an invite token or a migration path.

```sql
CREATE TABLE castlewatch_devices (
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
);

CREATE INDEX castlewatch_devices_family_lookup
ON castlewatch_devices (family_id, status, last_seen_at DESC);
```

`token_hash` stores a server-side hash of the device secret. The raw token is shown only once during setup and is never stored.

### `castlewatch_invites`

Short-lived invitations for onboarding a new device.

```sql
CREATE TABLE castlewatch_invites (
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
);

CREATE INDEX castlewatch_invites_family_lookup
ON castlewatch_invites (family_id, status, expires_at DESC);
```

Invites should default to short expiration such as 7 days.

## Authentication model

### Backward-compatible legacy mode

The existing `X-CastleWatch-Key` check remains valid while `legacy_family_key_enabled = TRUE`.

Legacy key access acts as `owner` for now because it already has full authority. When used, responses may include a gentle warning in a future GUI: `Legacy family key is still enabled`.

### Device-token mode

New clients send:

- `X-CastleWatch-Device-Token: cwdev_<prefix>_<secret>`

Server behavior:

1. Parse token prefix.
2. Find an active device by prefix.
3. Verify the full token against `token_hash` with constant-time comparison.
4. Confirm family and role.
5. Authorize operation.
6. Update `last_seen_at` only as part of the existing request transaction.

No raw token should appear in logs, JSON responses, exceptions, or UI.

## Authorization rules

| Operation | Owner | Editor | Viewer | Legacy key |
| --- | --- | --- | --- | --- |
| Read shared plan | yes | yes | yes | yes |
| Read history | yes | yes | yes | yes |
| Write shared plan | yes | yes | no | yes |
| Restore version | yes | yes | no | yes |
| Read operations report | yes | yes | no by default | yes |
| List devices | yes | no | no | yes during transition |
| Create invite | yes | no | no | yes during transition |
| Revoke device | yes | no | no | yes during transition |
| Disable legacy key | yes | no | no | no, requires device owner auth |

## Proposed endpoints

All endpoints remain under `/api/family-trip` unless a later design chooses a broader `/api/family` namespace.

### `GET /api/family-trip/devices`

Lists devices for the current family.

Returns only safe metadata:

```json
{
  "status": "ok",
  "devices": [
    {
      "id": "uuid",
      "displayName": "Ryan iPhone",
      "role": "owner",
      "status": "active",
      "createdAt": "...",
      "lastSeenAt": "...",
      "lastReadAt": "...",
      "lastWriteAt": "..."
    }
  ]
}
```

### `POST /api/family-trip/invites`

Creates a short-lived invite. Owner only.

Request:

```json
{
  "label": "Katie iPhone",
  "role": "editor"
}
```

Response shows the raw invite token once:

```json
{
  "status": "ok",
  "inviteToken": "cwinv_...",
  "expiresAt": "..."
}
```

### `POST /api/family-trip/devices/accept-invite`

Accepts an invite and creates a device token.

Request:

```json
{
  "inviteToken": "cwinv_...",
  "deviceName": "Katie iPhone"
}
```

Response shows the raw device token once:

```json
{
  "status": "ok",
  "deviceToken": "cwdev_...",
  "device": {
    "id": "uuid",
    "displayName": "Katie iPhone",
    "role": "editor"
  }
}
```

### `POST /api/family-trip/devices/revoke`

Revokes a device. Owner only.

Request:

```json
{
  "deviceId": "uuid"
}
```

### `POST /api/family-trip/devices/rename`

Renames the current device or a device managed by an owner.

Request:

```json
{
  "deviceId": "uuid",
  "displayName": "Ryan iPhone 17"
}
```

## Migration plan

### Step 1: design only

- Add this document.
- Review table and endpoint names.
- Confirm that the current family-key workflow remains untouched.

### Step 2: test-only helpers

- Add pure functions for token hashing, prefix extraction, and role checks.
- Unit test that tokens are never returned except on invite/device creation.
- No production routes yet.

### Step 3: additive schema setup

- Extend database setup with the new tables using `CREATE TABLE IF NOT EXISTS`.
- Seed the `family` workspace and owner placeholder.
- Do not alter `family_trip_state` or `family_trip_history`.

### Step 4: dual authorization

- Add a new authorization helper that accepts either the legacy family key or a valid device token.
- Existing endpoints continue to accept the current header.
- Tests prove current behavior is unchanged.

### Step 5: device endpoints

- Add list, invite, accept, revoke, and rename endpoints.
- Add tests for authorization, revocation, viewer blocking, and legacy compatibility.

### Step 6: frontend plumbing

- Add typed clients only.
- No visible GUI until approved.

### Step 7: minimal GUI

- Add device management under Shared Family Plan.
- Keep it visually consistent with the existing panel.

### Step 8: legacy key retirement option

- Allow the owner to disable legacy family-key access only after at least one active owner device exists.

## Railway and cost controls

- No separate request-log table.
- `last_seen_at`, `last_read_at`, and `last_write_at` should update only when a request already touches the database.
- Avoid heartbeat polling.
- Device list should be manual refresh only in the first GUI version.

## Security notes

- Store only hashes of device and invite secrets.
- Use constant-time comparisons for secrets.
- Include only token prefixes in metadata.
- Do not put tokens in URLs.
- Do not display existing tokens after creation.
- Device revocation should take effect immediately on the next request.
- A viewer token must not be able to write, restore, create invites, or view operations by default.

## Open questions

1. Should the first user-facing roles be only `owner` and `editor`, with `viewer` added later?
2. Should operations reports be owner-only or owner/editor?
3. Should invites expire after 24 hours, 7 days, or user-selected periods?
4. Should the GUI call them "family members" or "devices" first?
5. Should legacy key access remain permanent as an emergency backdoor, or should it eventually be disabled by default?

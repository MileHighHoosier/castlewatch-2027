# Accounts recovery and rollback plan

## Section 5 recovery boundary

CastleWatch now supports exactly one explicitly selected credential on shared-plan read, write, history, history-version, restore, Operations and device-management requests:

- the existing family key, which remains the owner-equivalent recovery path; or
- a protected device credential held in a `Secure`, `HttpOnly`, `SameSite=Strict` same-origin cookie.

The database `legacy_family_key_enabled` value is authoritative for every family-key request. Section 5 does not set it to `FALSE`, expose a retirement control or remove `CASTLEWATCH_FAMILY_KEY`. Section 5E production verification passed with an active protected Owner, a second real Editor/Viewer browser, explicit family-key recovery and rejected-cookie cleanup without hidden fallback.

## Current safe state

- `CASTLEWATCH_FAMILY_KEY` remains configured and the fixed `family` workspace keeps `legacy_family_key_enabled = TRUE`.
- The tested production Owner remains active; temporary Editor/Viewer devices are revoked.
- Owner and Editor devices may read, write, restore and use Operations; Viewer devices may read and inspect history only.
- A protected-device `401` expires the protected cookie, clears safe browser device metadata and records an explicit disconnected selection.
- CastleWatch never responds to rejected device access by silently selecting a saved family key.
- Revoking an account device never deletes or rewrites shared-plan state or history.
- No automatic family-key retirement is allowed.

## Recovery guarantees

A recovery or rollback must preserve these guarantees:

1. A valid family key can regain access while the authoritative database flag is enabled.
2. Shared trip data and history remain independent from device, member and invite rows.
3. A rejected or revoked raw device token is never restored or revealed; recovery creates a new credential.
4. The current device cannot revoke itself.
5. An owner device cannot revoke another owner device; owner-device revocation is restricted to the explicit family-key recovery path.
6. Raw family keys, device tokens, invite tokens, token hashes and pepper values never appear in responses, logs, issues or documentation.

## Browser recovery after a rejected or revoked device

Use this path when a browser reports that its protected device credential was rejected, revoked or missing.

1. Leave the browser disconnected. Do not expect CastleWatch to fall back automatically.
2. On a trusted owner browser, explicitly select family-key recovery or an active owner device.
3. Create a new Editor or Viewer invite for the replacement browser.
4. Accept the invite on the replacement browser. The new raw token is transferred once into protected cookie storage; only safe device metadata remains browser-readable.
5. Verify shared-plan access with the newly selected protected device.
6. From the trusted owner path, revoke the old device if it remains active.

If legacy raw-token migration fails, CastleWatch deliberately retains that legacy local token until protected storage is acknowledged. This exception prevents accidental credential loss during migration; it does not authorize fallback to the family key.

## Lost or revoked sole owner device

The normal device path cannot revoke itself or any owner device. Use the family-key recovery path for an owner replacement:

1. Confirm `CASTLEWATCH_FAMILY_KEY` remains configured and `legacy_family_key_enabled` remains `TRUE`.
2. Explicitly select family-key recovery on a trusted browser.
3. Revoke the lost owner device. The response must state that replacement bootstrap is required.
4. Bootstrap one replacement owner device through the confirmed owner-bootstrap action.
5. Store the returned one-time token only through the protected proxy flow.
6. Verify the replacement owner can read the shared plan and list devices before relying on device-only access.

Owner revocation and bootstrap lock the seeded owner member as a shared serialization point. Bootstrap still refuses to create a second active owner. The seeded member, shared plan and history are preserved throughout recovery.

## Authoritative legacy-gate recovery

Application routes only read `legacy_family_key_enabled`; Section 5D adds no route or UI that can change it. The production value must remain `TRUE`.

If an operator error changes the fixed workspace value to `FALSE`, valid family-key requests fail closed with `legacy_key_disabled`; active device credentials continue to use their server roles. Restore recovery access through an authenticated Railway PostgreSQL session:

```sql
UPDATE castlewatch_families
SET legacy_family_key_enabled = TRUE
WHERE id = 'family';
```

Verify that exactly the fixed `family` row is enabled, then test a read-only family-key request. Do not change or disclose the environment key, and do not alter `family_trip_state` or `family_trip_history`.

## Stable token-pepper contract

New device and invite credentials use this primary source:

1. non-empty `CASTLEWATCH_DEVICE_TOKEN_PEPPER`; otherwise
2. the existing `CASTLEWATCH_FAMILY_KEY` compatibility source.

Verification checks the primary source, optional `CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER`, and the current family-key compatibility source without logging any value. When an active device succeeds through a non-primary source, its stored HMAC is replaced atomically with one derived from the primary source in the same authorization transaction. Open invites may be accepted through the transition chain; the accepted device is always hashed with the primary source.

### Introduce a dedicated stable pepper

1. Generate and store a stable secret directly in the Railway environment as `CASTLEWATCH_DEVICE_TOKEN_PEPPER`; never put it in source, chat, CI output or documentation.
2. Keep `CASTLEWATCH_FAMILY_KEY` unchanged. Existing family-key-derived device tokens remain valid through the compatibility verifier and migrate on successful use.
3. Deploy and verify active devices plus any open invites before changing either secret source.
4. Keep the family key configured and the database legacy flag enabled.

### Rotate the dedicated pepper

1. Keep the old value available only in the secret manager.
2. Set the new value as `CASTLEWATCH_DEVICE_TOKEN_PEPPER` and the old value as `CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER` in one deployment change.
3. Verify owner recovery first, then exercise each active device and any still-valid invite. Successful active-device authorization rehashes that token to the new primary.
4. Do not remove the previous pepper until every active device has either succeeded, been intentionally reconnected or been revoked, and all invites created with the old source have been accepted or expired.
5. Remove `CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER` in a separate change after verification.

### Roll back a pepper rotation

While the 5D transition verifier is deployed, swap the environment roles: restore the old value as `CASTLEWATCH_DEVICE_TOKEN_PEPPER` and temporarily place the attempted new value in `CASTLEWATCH_DEVICE_TOKEN_PREVIOUS_PEPPER`. Successful devices rehash back to the restored primary.

If application code must also be rolled back, keep the pepper that currently hashes active tokens configured as `CASTLEWATCH_DEVICE_TOKEN_PEPPER`; the pre-5D code understands that primary variable but not the previous-pepper transition. Never roll back the code and primary secret blindly at the same time.

## Backend rollback path

Use this path if the 5D backend change causes production authorization problems.

1. Keep `CASTLEWATCH_FAMILY_KEY`, the current primary pepper and `legacy_family_key_enabled = TRUE` unchanged.
2. Preserve all shared-plan and account tables.
3. Roll back the application commit without rolling back database data.
4. Verify family-key read, history, restore and Operations paths.
5. Verify current shared-plan version and retained history before attempting device recovery.
6. If active device hashes already migrated to a new primary, keep that primary configured during the code rollback.

Tables that must not be removed during a normal rollback:

- `family_trip_state`
- `family_trip_history`
- `castlewatch_families`
- `castlewatch_members`
- `castlewatch_devices`
- `castlewatch_invites`

## Frontend rollback path

Use this path if rejected-credential cleanup or the Family devices panel causes a production UI problem.

1. Keep the backend and family-key recovery path available.
2. Roll back the frontend commit and verify the production build.
3. Explicitly select family-key recovery; do not assume an older frontend will clear a protected cookie after every normal-route `401`.
4. Use the Family devices clear action, or expire the narrowly scoped protected cookie through the same-origin proxy, before reconnecting a replacement device.
5. Verify shared-plan read and history before write or restore actions.

## Token and invite recovery rules

- A raw device token cannot be recovered after acceptance because it is intentionally returned only once.
- If a device token is lost or rejected, create a new invite and new credential.
- If an invite token is lost or expired, create a new invite.
- If a phone is sold, lost or replaced, revoke its server-side device record from an owner path.
- Device-list and recovery responses must never include raw tokens, hashes or pepper values.
- Revocation must deny the old token on device management and every normal shared-plan endpoint without changing the shared-plan document or history.

## Non-retirement gate

Do not build or enable a family-key retirement option until every prerequisite in `accounts_migration_contract.md` passes and the user separately authorizes that work. Starting or finalizing Section 5D or 5E is not retirement approval.

## Rollback success criteria

A rollback is successful when:

- the enabled family-key recovery path can read the shared plan;
- current shared-plan data, version history and restore behavior are intact;
- Operations remains available to an authorized owner path;
- rejected or revoked device credentials do not cause silent family-key fallback;
- an owner replacement can be bootstrapped without exposing a credential;
- no account rollback deletes trip data; and
- the family key remains configured and the production legacy flag remains enabled.

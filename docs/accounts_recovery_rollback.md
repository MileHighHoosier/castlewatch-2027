# Accounts recovery and rollback plan

This plan documents how to recover from device-management problems and how to roll back safely before any future legacy family-key retirement option is considered.

## Current safe state

- The current `CASTLEWATCH_FAMILY_KEY` path remains enabled.
- Existing shared-plan read, write, history, restore, and operations routes still use the family key.
- Device/invite routes are additive.
- Device tokens do not replace the family key.
- No automatic family-key retirement is allowed.

## Recovery goals

A recovery path must preserve these guarantees:

1. The user can regain access with the existing family key.
2. Shared trip data and history are not deleted.
3. Device records can be ignored, revoked, or rebuilt without touching shared-plan data.
4. Any future family-key disablement must be reversible by configuration or database flag.
5. Raw device tokens and token hashes must not be exposed in recovery responses or logs.

## User-facing recovery path

Use this path when a browser loses access, a phone is replaced, an invite expires, or a saved device token is cleared.

1. Use the existing family key on a trusted owner browser.
2. Open the production app and connect Shared Family Plan.
3. Open Family devices.
4. Create a new invite for the replacement browser or phone.
5. Accept the invite on the replacement browser or phone.
6. Refresh the device list from the owner browser.
7. Revoke the old or lost device if it still appears.

Expected result: the replacement browser is connected and the old device no longer has active device-token access.

## Emergency recovery path

Use this path if the device-management UI breaks or all device tokens fail.

1. Keep the production `CASTLEWATCH_FAMILY_KEY` configured.
2. Use the existing Shared Family Plan family-key flow.
3. Do not attempt family-key retirement.
4. Treat device access as temporarily unavailable.
5. Deploy a frontend rollback or backend rollback if the Family devices panel or routes interfere with normal sync.

Expected result: the shared plan remains usable through the legacy family-key flow while device-management issues are fixed.

## Backend rollback path

Use this path if device/invite backend routes cause production issues.

1. Revert the backend PR that registered device/invite routes.
2. Leave additive account/device tables in place unless there is a proven need to remove them.
3. Confirm `/api/family-trip`, `/api/family-trip/history`, `/api/family-trip/restore`, and `/api/family-trip/operations` still work with `CASTLEWATCH_FAMILY_KEY`.
4. Confirm device/invite routes are unavailable or no longer referenced.
5. Do not delete shared-plan tables or history.

Tables that should not be touched during normal rollback:

- `family_trip_state`
- `family_trip_history`

Additive account tables may remain dormant:

- `castlewatch_families`
- `castlewatch_members`
- `castlewatch_devices`
- `castlewatch_invites`

## Frontend rollback path

Use this path if the Family devices panel causes production UI problems.

1. Revert the frontend PR that added the `FamilyTripDevices` component and its import.
2. Keep the existing Shared Family Plan component.
3. Keep the Operations link unchanged.
4. Confirm the app builds.
5. Confirm Shared Family Plan still loads and syncs with the family key.

Expected result: the app returns to the previous Shared Family Plan behavior while backend device/invite routes can remain unused.

## Token and invite recovery rules

- A device token cannot be recovered after acceptance because it is intentionally returned only once.
- If a device token is lost, create a new invite and connect a new device.
- If an invite token is lost, create a new invite.
- If an invite expires, create a new invite.
- If a phone is sold, lost, or replaced, revoke the old device record from an owner browser.
- Device-list responses must never include raw tokens or token hashes.

## Future family-key retirement prerequisites

Do not build or enable a family-key retirement option until all of these are true:

1. The production manual verification checklist passes.
2. At least one owner device exists.
3. The owner device has been manually tested in production.
4. The user confirms the owner device can list, rename, and revoke devices.
5. The user confirms family-key Shared Family Plan sync still works before retirement work begins.
6. This recovery and rollback plan has been reviewed.
7. The next change adds only an owner-controlled option; it must not disable the family key by default.
8. The user explicitly authorizes the retirement-option implementation.

## First retirement-option implementation limit

The first implementation may only add an owner-controlled setting or route that can disable legacy family-key access later.

It must not:

- automatically disable the family key;
- delete the family key from environment configuration;
- delete shared-plan or history data;
- remove the fallback code path before rollback is proven;
- remove the ability to re-enable the family key by database flag or deployment rollback.

## Rollback success criteria

A rollback is successful when:

- Shared Family Plan connects with the family key;
- current shared plan data loads;
- history/restore still works;
- operations still works;
- no device-management failure blocks normal trip planning;
- no family-key retirement behavior remains active unless explicitly authorized and verified.

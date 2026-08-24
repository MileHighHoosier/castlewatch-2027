# Section 5 accounts and device migration contract

## Status

**Section 5A finalized on August 24, 2026 — Section 5B next and not started.**

This document records the August 24, 2026 cross-repository audit of the deployed accounts, invitations and device-management foundation. Section 5A is documentation and planning only: it does not change production authorization, database state, browser credentials, dependencies, runtime configuration or user-visible behavior.

Audited production checkpoints:

- backend `main`: `974dda9c639ca54417fca1be1b0ac2c1214a9c0b`;
- frontend `main`: `416e8d0deb3c4740f046dd0afa6f9cfe0377cca3`;
- existing phase tracker: backend issue #10;
- existing production-verification tracker: frontend issue #25.

Section 5A closeout evidence:

- backend PR #44 was squash-merged at `8d970cfff75d6b859e3b242f5d0b0d312d0151c5`;
- exact-head Python 3.12.14 CI passed clean dependency installation, all 69 backend contracts and full production-module compilation;
- the audited frontend head passed all 82 contracts and the production Next.js build;
- the documentation-only backend merge deployed successfully to Railway;
- no production authorization, schema, data, credential, dependency, runtime, itinerary, account state or frontend behavior changed.

The historical design in `accounts_device_model.md`, the approval history in `accounts_authorization_gates.md`, and the recovery plan in `accounts_recovery_rollback.md` remain supporting references. This contract governs the remaining Section 5 work when their old future-tense wording conflicts with deployed code.

## Section 5 goal

Finish the existing **private-family, device-based** migration so a verified owner device and invited Editor/Viewer devices can use the normal shared-plan system with enforceable roles and recoverable revocation.

Section 5 does not introduce public accounts, passwords, social login, SMS delivery, automatic polling or a general multi-family product. The existing fixed `family` workspace and shared-trip version/history model remain unchanged.

Completing Section 5 does **not** authorize family-key retirement. `CASTLEWATCH_FAMILY_KEY` must remain configured and enabled unless a later, separate user approval explicitly authorizes an owner-controlled retirement option after every prerequisite in this contract passes.

## Verified implemented foundation

### Backend

- additive `castlewatch_families`, `castlewatch_members`, `castlewatch_devices` and `castlewatch_invites` tables;
- seeded `family` workspace and placeholder owner member;
- hashed `cwdev_` device credentials and `cwinv_` invite credentials with constant-time verification;
- owner/editor/viewer permission helpers;
- safe device/invite serialization that excludes raw tokens and hashes;
- device access-state, list, invite-create, atomic invite-accept, rename and revoke routes;
- immediate rejection of revoked device tokens on device-management routes;
- current family-key owner compatibility;
- focused helper, route, atomicity and credential-safety contracts.

### Frontend

- same-origin Vercel proxy actions and typed clients for device-management routes;
- manual Family devices UI for access checks, invite creation/acceptance, rename and revoke;
- one-time invite display and non-display of the accepted raw device token;
- browser storage record `castlewatch.family-device-access.v1`;
- explicit family-key, device-token and revoked-token access-state presentation;
- migration guidance, credential-state diagnostics and a production proxy smoke;
- partial production verification recorded in frontend issue #25.

## Verified current gaps

1. **No owner-device bootstrap exists.** Production invites are limited to Editor and Viewer, accepted devices have no member association, and the only owner-device record in tests is manually seeded test data. The required active owner device cannot currently be created through the product.
2. **Normal shared-plan operations are still family-key-only.** Backend read, write, history, history-version, restore and operations handlers use `family_trip._authorization_error`; they do not call the device authorization layer.
3. **The frontend enforces the same legacy-only boundary.** The shared proxy's `legacyKeyOnly` guard rejects device credentials for read/write/history/restore/operations, and sync/history/autosave/operations clients accept a family-key string rather than an authorization object.
4. **Role helpers are not enforced on normal shared-plan operations.** Existing tests prove helper behavior and device-management restrictions, but not the Owner/Editor/Viewer matrix across normal read, write, history, restore and operations routes.
5. **`legacy_family_key_enabled` is stored but not authoritative.** No production authorization path reads the database flag. Section 5 must make its meaning testable while leaving its production value `TRUE`.
6. **Credential selection masks device access.** Both browser device management and the Vercel proxy prefer the family key when both credentials are present. That makes a browser with the family key unsuitable for a clean revoked-device or device-only verification.
7. **Raw device credentials are still persisted in `localStorage`.** Expanding that credential to normal shared-plan operations would increase the impact of any frontend script injection unless the credential boundary is hardened first.
8. **Token-pepper continuity is not explicit.** The backend uses `CASTLEWATCH_DEVICE_TOKEN_PEPPER` when configured and otherwise falls back to `CASTLEWATCH_FAMILY_KEY`; changing that source can invalidate existing device tokens. No secret value belongs in documentation or test output, but the configuration state and rotation procedure must be resolved before retirement can be considered.
9. **Production verification is incomplete.** Issue #25 confirms several family-key, invite, rename, revoke and UI paths, but the clean revoked-token-only rejection, active owner-device path, device-authorized normal sync and full role matrix have not passed in production.
10. **A legacy direct frontend proxy remains key-only.** `app/api/family-trip/route.ts` has no current in-repository caller and should not be silently promoted or removed during migration work; later implementation must either keep it safely compatible or explicitly classify it as cleanup.

## Current and target authorization matrix

| Operation | Current family key | Current device token | Section 5 target |
| --- | --- | --- | --- |
| Read shared plan | Owner-equivalent | Not accepted | Owner, Editor, Viewer |
| Read history/version | Owner-equivalent | Not accepted | Owner, Editor, Viewer |
| Write shared plan | Owner-equivalent | Not accepted | Owner, Editor |
| Restore history | Owner-equivalent | Not accepted | Owner, Editor |
| Read Operations | Owner-equivalent | Not accepted | Owner, Editor |
| Check device access | Owner | Any active device; revoked state is explicit | Preserve |
| List devices | Owner | Owner only | Preserve |
| Create invite | Owner | Owner only | Preserve; Editor/Viewer invites only |
| Rename device | Owner-equivalent; may rename any device | Current active device; Owner may rename others | Preserve |
| Revoke device | Owner | Owner only; current device cannot revoke itself | Preserve and add last-owner safety |
| Accept invite | Invite token | Invite token | Preserve atomic one-time use |
| Bootstrap owner device | No route | No route | Explicit family-key recovery path only |

The role assigned by the verified server record is authoritative. Browser-stored role/name metadata is display-only and must never grant permission.

## Migration architecture decisions

### One credential per request

The Vercel proxy must forward exactly one authorization credential. Once a device credential has been verified and selected, CastleWatch must not silently fall back from a rejected or revoked device token to the family key. Recovery through the family key must be an explicit user action so revocation remains observable and testable.

### Protected browser credential boundary

Before device tokens authorize normal shared-plan actions, the accepted raw token must move out of JavaScript-readable long-term storage into a `Secure`, `HttpOnly`, `SameSite=Strict` cookie managed by the same-origin Vercel proxy and scoped to the narrow shared-family proxy path. State-changing proxy requests must retain strict method/content-type validation and verify their same-origin context. Safe device metadata may remain browser-readable. Migration from the existing `castlewatch.family-device-access.v1` record must be one-time, acknowledged by the server, and remove the raw local token only after the protected credential is established.

The family-key path remains backward-compatible throughout Section 5. Any change to its browser storage must be independently regression-tested and must not remove the recovery path.

### Owner bootstrap

The first active owner device must be created only from a valid family-key recovery session through an explicit, confirmed bootstrap action. It must:

- create an `owner` device tied to the seeded owner member;
- return the raw device credential only to the protected proxy setup flow;
- store and display only safe metadata afterward;
- avoid creating an owner through a normal Editor/Viewer invite;
- remain recoverable through the family key;
- never change `legacy_family_key_enabled`.

### Shared-plan authorization

Backend normal shared-plan handlers must use the common authorization layer inside the existing transaction boundary with the permission shown in the target matrix. Existing version locking, optimistic conflicts, history retention, payload limits and restore-as-new-version behavior must remain unchanged.

Frontend sync, history, autosave and operations clients must use one typed authorization abstraction. Viewer sessions must not offer or attempt write, restore, or operations actions. Server enforcement remains mandatory even when the UI hides a control.

### Legacy-key flag and recovery

`legacy_family_key_enabled` must become an authoritative, tested server-side gate, but Section 5 must not set it to `FALSE`, expose a retirement control, remove the environment key or delete the fallback path. A valid family key must continue to recover access while the flag is true.

Revocation must reject the device across device management and every normal shared-plan endpoint. Recovery must create a new credential rather than reveal or restore an old raw token. Shared-plan state/history must remain independent from account/device rows and survive any device rollback.

### Pepper continuity

Implementation must distinguish new-token hashing from legacy-token verification without disclosing either secret. Before production owner bootstrap, the deployment must have a documented stable pepper source or a backward-compatible verification transition. A pepper change must never be bundled with family-key retirement or silently invalidate the only verified owner device.

## Section 5 batches

### 5A — Architecture audit and migration contract

Status: **Complete — merged and production-deployed August 24, 2026.**

Deliverables:

- reconcile deployed backend/frontend behavior with issues #10 and #25;
- record the implemented inventory, remaining gaps and authorization matrix;
- define credential, owner-bootstrap, role, recovery and non-retirement boundaries;
- replace stale next-step instructions in the historical account documents;
- make no production behavior, schema, credential, dependency or runtime change.

### 5B — Owner-device bootstrap and protected credential foundation

Deliverables:

- family-key-authorized owner bootstrap with safe one-time credential handling;
- protected same-origin credential cookie and one-time migration from the existing local device-token record;
- explicit credential selection with no silent revoked-token fallback;
- backend/frontend contracts for bootstrap, storage cleanup, safe metadata and unchanged family-key recovery;
- no normal shared-plan role switch and no legacy-key disablement.

### 5C — Normal shared-plan dual authorization and role enforcement

Deliverables:

- device-token authorization for read/write/history/history-version/restore/operations;
- exact Owner/Editor/Viewer server-side matrix and matching frontend controls;
- device-aware manual sync, guarded autosave, history and Operations flows;
- regression proof that existing family-key behavior and trip version/conflict/history semantics remain unchanged;
- no legacy-key disablement.

### 5D — Revocation, recovery and legacy-gate hardening

Deliverables:

- revoked-token denial across every protected endpoint without silent fallback;
- owner/recovery and last-owner safety contracts;
- authoritative read enforcement for `legacy_family_key_enabled` while its production value remains enabled;
- stable token-pepper/rotation and rollback procedure;
- updated recovery documentation and automated regression coverage;
- no retirement UI or flag change.

### 5E — Production two-device verification and Section 5 closeout

Deliverables:

- update and complete frontend issue #25 against the finished authorization model;
- verify family-key recovery, active owner device, Editor and Viewer boundaries, normal shared-plan sync/history/restore/operations behavior, rename, revoke and revoked-token-only rejection on real devices;
- verify Railway and the real `castlewatch-frontend` Vercel project;
- record evidence in canonical project state and close Section 5 trackers;
- leave `CASTLEWATCH_FAMILY_KEY` enabled.

## Non-retirement gate

Section 5 may close with the family key still enabled. A later retirement option may only be proposed after all of the following are true:

1. an active owner device exists and is manually verified;
2. normal device-authorized shared-plan read/write/history/restore/operations flows pass their role contracts;
3. Editor and Viewer permissions pass automated and production checks;
4. revocation is verified without a hidden family-key fallback;
5. recovery and rollback are verified while the family key remains available;
6. token-pepper continuity and last-owner safety are proven;
7. production two-device verification passes;
8. the user separately and explicitly authorizes an owner-controlled retirement option.

No Section 5 start/finalize instruction constitutes item 8.

## Invariants for every Section 5 batch

- Preserve the October 9–16, 2027 trip, two-adult/two-child profile and no-park-hopping rule.
- Preserve **Keep / Swap / Wait / Review** decision outputs and user-approved itinerary mutation.
- Do not expose a family key, raw device token, raw invite token, token hash or pepper in source, logs, issues, CI output or long-lived UI.
- Do not change dependency/runtime versions or lockfiles as incidental migration work.
- Do not delete or destructively alter shared-plan, history, account or device data.
- Keep changes incremental, reversible and separately approved with **Start** / **Finalize** checkpoints.
- Do not pull Section 6 production-wide smoke testing or Section 8 product development into Section 5.

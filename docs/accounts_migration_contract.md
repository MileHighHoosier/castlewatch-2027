# Section 5 accounts and device migration contract

## Status

**Section 5 finalized and production-verified on August 29, 2026.**

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

Section 5B closeout evidence:

- backend PR #46 was squash-merged at `5456a272041f2d329b26ff7cd4b1a338e8960d51`, and Railway succeeded;
- frontend PR #39 was squash-merged at `c7b2159d7774ce6d01682626f71da4a2f2dc5dfb`, and the real `castlewatch-frontend` Vercel production deployment succeeded;
- exact-head Python 3.12.14 CI passed clean dependency installation, all 79 backend contracts and production-module compilation;
- exact-head Node 22 CI passed clean dependency installation, all 90 frontend contracts, the production build and mobile browser smoke;
- the owner-bootstrap and protected-credential foundation is deployed without creating a production owner device or enabling device credentials for normal shared-plan operations;
- no schema/data, dependency/runtime, itinerary, reservation, park-order or automatic-plan change occurred, and `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

Section 5C closeout evidence:

- backend PR #48 was squash-merged at `d8b7fa630cbd2a20a77044b04c5d1f3ae9565918`, and Railway succeeded;
- frontend PR #40 was squash-merged at `283b0da71b4a540c74e09360d5b599b8ecc57086`, and the real `castlewatch-frontend` Vercel production deployment succeeded;
- exact-head Python 3.12.14 CI passed clean dependency installation, all 82 backend contracts and production-module compilation;
- exact-head Node 22 CI passed clean dependency installation, all 99 frontend contracts, the production build and mobile browser smoke;
- normal shared-plan read, history, history-version, write, restore and Operations routes now enforce the exact Owner/Editor/Viewer device-role matrix while retaining explicit family-key recovery;
- no production owner-device record, schema/data, dependency/runtime, itinerary, reservation, park-order, legacy-key flag, pepper or last-owner change occurred, and `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

Section 5D closeout evidence:

- backend PR #50 was squash-merged at `79094f56af9b8d0be18fae6e518365d6775bd35a`, and Railway plus the production health endpoint succeeded;
- frontend PR #41 was squash-merged at `f591f5b140e5ca0654f04a1433963d7ba560bd71`, and the real `castlewatch-frontend` Vercel production deployment succeeded;
- exact-head Python 3.12.14 CI passed clean dependency installation, all 90 backend contracts and full production-module compilation;
- exact-head Node 22 CI passed clean dependency installation, all 104 frontend contracts, the production build and mobile browser smoke;
- revoked credentials are denied across device management and normal shared-plan routes, the enabled legacy-key flag is authoritative, owner recovery is serialized, and pepper transition/rollback plus protected-cookie failure cleanup are regression-protected;
- no production device, secret or pepper environment value, legacy-key flag value, schema/data, dependency/runtime, itinerary, reservation, park-order or retirement behavior changed, and `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

Section 5E closeout evidence:

- frontend PR #42 merged at `fe964bec64f1d2071c899e2ea5d8bf3d79a1e949`, frontend PR #43 merged at `f87f5b761cb0cec7c74defad723a3790bf85a6fd`, and frontend PR #44 merged at `f7b5ccbf38081ff044808899ef7c965c2e04e1cd`;
- the frontend verification head passed all 111 tests and the production build, and its authoritative Vercel deployment succeeded;
- family-key recovery, protected Owner persistence and a second real no-family-key Editor/Viewer browser passed their production role contracts;
- self-rename, Owner-managed revocation and revoked-cookie-only cleanup passed without hidden family-key fallback;
- content-identical backup/restore verification preserved append-only history, and a final deliberate trip-name cleanup created shared version 17 through the optimistic upload confirmation;
- the October 9–16, 2027 two-adult/two-child, no-park-hopping trip profile, zero bookings and manual **Wait / Keep the base plan provisional** recommendation state remained intact;
- the tested Owner remains active, temporary Editor/Viewer devices are revoked, Railway health and the authoritative frontend deployment are green, and device rows contain safe metadata only;
- no raw credential/secret, dependency/runtime, schema, itinerary order, reservation, automatic recommendation, legacy-key flag or family-key retirement change was included.

The historical design in `accounts_device_model.md`, the approval history in `accounts_authorization_gates.md`, and the recovery plan in `accounts_recovery_rollback.md` remain supporting references. This contract records the completed Section 5 boundary when their old future-tense wording conflicts with deployed code.

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
- explicit family-key-only owner bootstrap tied to the seeded owner member with active-owner conflict protection and revoked-owner replacement;
- non-cacheable bootstrap and invite-acceptance one-time credential responses;
- immediate rejection of revoked device tokens on device-management routes;
- revoked-device denial across every normal shared-plan route without mutation or family-key fallback;
- normal shared-plan read, history, history-version, write, restore and Operations authorization through the common family-key/device-token layer;
- exact Owner/Editor/Viewer permission enforcement inside the existing shared-plan transaction boundary;
- authoritative `legacy_family_key_enabled` enforcement across family-key device-management and shared-plan requests;
- transaction-serialized owner-device revocation restricted to explicit family-key recovery before replacement bootstrap;
- primary/previous/family-key compatibility pepper verification with successful-use rehash for active devices and open invites;
- rejection of ambiguous two-credential requests and devices outside the fixed `family` workspace;
- current family-key owner compatibility;
- focused helper, route, atomicity and credential-safety contracts.

### Frontend

- same-origin Vercel proxy actions and typed clients for device-management routes;
- manual Family devices UI for confirmed owner bootstrap, access checks, invite creation/acceptance, rename and revoke;
- narrow `Secure`, `HttpOnly`, `SameSite=Strict` proxy-managed device credential cookie;
- one-time invite/bootstrap credentials stripped before setup responses reach browser JavaScript;
- acknowledged migration from the legacy `castlewatch.family-device-access.v1` raw-token record, with safe display metadata retained and the raw token removed only after success;
- explicit family-key, protected-device and revoked-device access-state presentation without silent fallback;
- selected protected-cookie `401` cleanup that expires the cookie, clears safe device metadata and records an explicit disconnected selection;
- one typed authorization abstraction across manual sync, guarded autosave, history/version/restore and Operations;
- role-aware controls that keep Viewer sessions read/history-only while Owner and Editor sessions may write, restore and use Operations;
- strict same-origin JSON validation plus device-token and token-hash response scrubbing;
- migration guidance, credential-state diagnostics and a production proxy smoke;
- completed production verification recorded in frontend issue #25.

## Verified final boundary

1. **Production migration acceptance passed.** A protected production Owner and a second real Editor/Viewer browser passed bootstrap, persistence, normal shared-plan authorization, role enforcement, self-rename, revocation, recovery and rejected-cookie cleanup.
2. **Family-key recovery remains part of the architecture.** `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` remain configured and enabled; Section 5 finalization is not retirement approval.
3. **A legacy direct frontend proxy remains key-only.** `app/api/family-trip/route.ts` has no current in-repository caller and should not be silently promoted or removed; later work must either keep it safely compatible or explicitly classify it as cleanup.

Section 5B closed the prior credential-selection and JavaScript-readable long-term device-token gaps: device-management requests now select one explicit credential, and acknowledged device credentials are held by the narrow protected proxy cookie. A failed legacy migration deliberately retains its raw local token for explicit recovery rather than silently losing access.

Section 5C closed the normal-route dual-authorization and role-enforcement gaps: the backend authorizes the selected credential inside existing shared-plan transactions, and the frontend uses one explicit typed credential selection across normal family flows. Browser role metadata remains display-only and the server-side device record remains authoritative.

Section 5D closed the authoritative legacy-gate, revoked-credential, owner-recovery and pepper-continuity gaps. The selected protected-cookie failure path also clears the cookie and safe metadata into an explicit disconnected state without family-key fallback. Section 5E then completed production device creation and real-device verification without changing those boundaries.

## Current and target authorization matrix

| Operation | Current family key | Current device token | Section 5 target |
| --- | --- | --- | --- |
| Read shared plan | Owner-equivalent | Owner, Editor, Viewer | Preserve |
| Read history/version | Owner-equivalent | Owner, Editor, Viewer | Preserve |
| Write shared plan | Owner-equivalent | Owner, Editor | Preserve |
| Restore history | Owner-equivalent | Owner, Editor | Preserve |
| Read Operations | Owner-equivalent | Owner, Editor | Preserve |
| Check device access | Owner | Any active device; revoked state is explicit | Preserve |
| List devices | Owner | Owner only | Preserve |
| Create invite | Owner | Owner only | Preserve; Editor/Viewer invites only |
| Rename device | Owner-equivalent; may rename any device | Current active device; Owner may rename others | Preserve |
| Revoke device | Owner; owner-device revocation is the explicit recovery path | Owner only; current device cannot revoke itself or an owner device | Preserve |
| Accept invite | Invite token | Invite token | Preserve atomic one-time use |
| Bootstrap owner device | Explicit recovery path | Not accepted | Preserve |

The role assigned by the verified server record is authoritative. Browser-stored role/name metadata is display-only and must never grant permission.

## Migration architecture decisions

### One credential per request

The Vercel proxy must forward exactly one authorization credential. Once a device credential has been verified and selected, CastleWatch must not silently fall back from a rejected or revoked device token to the family key. Recovery through the family key must be an explicit user action so revocation remains observable and testable.

### Protected browser credential boundary

Section 5B moved acknowledged device credentials out of JavaScript-readable long-term storage into a `Secure`, `HttpOnly`, `SameSite=Strict` cookie managed by the same-origin Vercel proxy and scoped to the narrow shared-family proxy path. The proxy enforces JSON and same-origin context, removes raw credentials and hashes from browser responses, and keeps only safe device metadata browser-readable. Migration from the legacy `castlewatch.family-device-access.v1` raw-token record is one-time and server-acknowledged; the raw local token is removed only after the protected credential is established.

The family-key path remains backward-compatible throughout Section 5. Any change to its browser storage must be independently regression-tested and must not remove the recovery path.

### Owner bootstrap

The first active owner device must be created only from a valid family-key recovery session through an explicit, confirmed bootstrap action. It must:

- create an `owner` device tied to the seeded owner member;
- return the raw device credential only to the protected proxy setup flow;
- store and display only safe metadata afterward;
- avoid creating an owner through a normal Editor/Viewer invite;
- remain recoverable through the family key;
- never change `legacy_family_key_enabled`.

Section 5B implements this bootstrap contract. Section 5E invoked and verified it in production; the protected Owner remains active and the recovery path remains enabled.

### Shared-plan authorization

Backend normal shared-plan handlers use the common authorization layer inside the existing transaction boundary with the permission shown in the target matrix. Existing version locking, optimistic conflicts, history retention, payload limits and restore-as-new-version behavior remain unchanged.

Frontend sync, history, autosave and operations clients use one typed authorization abstraction. Viewer sessions do not offer or attempt write, restore, or Operations actions. Server enforcement remains mandatory even when the UI hides a control.

### Legacy-key flag and recovery

`legacy_family_key_enabled` is an authoritative, tested server-side gate for every family-key request. Section 5D did not set it to `FALSE`, expose a retirement control, remove the environment key or delete the recovery path. A valid family key continues to recover access while the flag is true.

Revocation rejects the device across device management and every normal shared-plan endpoint. Recovery creates a new credential rather than revealing or restoring an old raw token. Owner-device revocation is restricted to the explicit family-key recovery path and serialized before replacement bootstrap. Shared-plan state/history remains independent from account/device rows and survives device rollback.

### Pepper continuity

New credentials use the primary pepper. Verification temporarily accepts a configured previous pepper and the family-key compatibility source without disclosing any value, then rehashes active device credentials to the primary pepper after successful use; open invites survive the same transition. `docs/accounts_recovery_rollback.md` defines introduction, rotation and rollback order. A pepper change must never be bundled with family-key retirement or silently invalidate the only verified owner device.

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

Status: **Complete — merged and production-deployed August 24, 2026.**

Deliverables:

- family-key-authorized owner bootstrap with safe one-time credential handling;
- protected same-origin credential cookie and one-time migration from the existing local device-token record;
- explicit credential selection with no silent revoked-token fallback;
- backend/frontend contracts for bootstrap, storage cleanup, safe metadata and unchanged family-key recovery;
- no normal shared-plan role switch and no legacy-key disablement.

Completion evidence:

- backend PR #46 merged at `5456a272041f2d329b26ff7cd4b1a338e8960d51`; Python 3.12.14 CI passed all 79 contracts and compilation, and Railway succeeded;
- frontend PR #39 merged at `c7b2159d7774ce6d01682626f71da4a2f2dc5dfb`; Node 22 CI passed all 90 contracts, production build and mobile browser smoke, and the real frontend Vercel production deployment succeeded;
- no production owner-device record was created, normal shared-plan actions remain family-key-only, and the family key remains enabled.

### 5C — Normal shared-plan dual authorization and role enforcement

Status: **Complete — merged and production-deployed August 24, 2026.**

Deliverables:

- device-token authorization for read/write/history/history-version/restore/operations;
- exact Owner/Editor/Viewer server-side matrix and matching frontend controls;
- device-aware manual sync, guarded autosave, history and Operations flows;
- regression proof that existing family-key behavior and trip version/conflict/history semantics remain unchanged;
- no legacy-key disablement.

Completion evidence:

- backend PR #48 merged at `d8b7fa630cbd2a20a77044b04c5d1f3ae9565918`; Python 3.12.14 CI passed all 82 contracts and compilation, and Railway succeeded;
- frontend PR #40 merged at `283b0da71b4a540c74e09360d5b599b8ecc57086`; Node 22 CI passed all 99 contracts, production build and mobile browser smoke, and the real frontend Vercel production deployment succeeded;
- family-key behavior, optimistic conflicts, history retention, payload limits and restore-as-new-version behavior remain protected;
- 5D legacy-gate, pepper, recovery and last-owner work remained separate from 5C; 5E production device verification remains separate from both.

### 5D — Revocation, recovery and legacy-gate hardening

Status: **Complete — merged and production-deployed August 24, 2026.**

Deliverables:

- revoked-token denial across every protected endpoint without silent fallback;
- owner/recovery and last-owner safety contracts;
- authoritative read enforcement for `legacy_family_key_enabled` while its production value remains enabled;
- stable token-pepper/rotation and rollback procedure;
- updated recovery documentation and automated regression coverage;
- no retirement UI or flag change.

Completion evidence:

- backend PR #50 merged at `79094f56af9b8d0be18fae6e518365d6775bd35a`; Python 3.12.14 CI passed all 90 contracts and full production-module compilation, and Railway plus the production health endpoint succeeded;
- frontend PR #41 merged at `f591f5b140e5ca0654f04a1433963d7ba560bd71`; Node 22 CI passed all 104 contracts, the production build and mobile browser smoke, and the real frontend Vercel production deployment succeeded;
- revoked-device denial, authoritative enabled legacy-gate behavior, family-key-only owner recovery, pepper transition/rollback and selected protected-cookie failure cleanup are automated and deployed;
- no production owner-device record was created, and no secret/pepper environment value, legacy-key flag value, schema/data, dependency/runtime, itinerary, reservation, park-order or retirement behavior changed;
- 5E production device creation and two-device verification remain separate, and the family key remains configured and enabled.

### 5E — Production two-device verification and Section 5 closeout

Status: **Complete — production-verified August 29, 2026.**

Deliverables:

- update and complete frontend issue #25 against the finished authorization model;
- verify family-key recovery, active owner device, Editor and Viewer boundaries, normal shared-plan sync/history/restore/operations behavior, rename, revoke and revoked-token-only rejection on real devices;
- verify Railway and the real `castlewatch-frontend` Vercel project;
- record evidence in canonical project state and close Section 5 trackers;
- leave `CASTLEWATCH_FAMILY_KEY` enabled.

Completion evidence:

- frontend PRs #42–#44 merged at `fe964bec64f1d2071c899e2ea5d8bf3d79a1e949`, `f87f5b761cb0cec7c74defad723a3790bf85a6fd` and `f7b5ccbf38081ff044808899ef7c965c2e04e1cd`;
- all 111 frontend tests and the production build passed at the verification head, and the authoritative Vercel deployment succeeded;
- the live Owner/Editor/Viewer, family-key recovery, normal shared-plan, history/restore/Operations, rename, revoke and revoked-cookie-only scenarios passed on production devices;
- final shared version 17 is up to date with history intact, guarded autosave off and the trip/profile/recommendation invariants preserved;
- Railway health remained green, the active production Owner remains protected, temporary devices are revoked, and no credential material was persisted in verification evidence;
- `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` remain configured and enabled.

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

Section 5E verified items 1–7. Item 8 has not been granted, so retirement remains unauthorized.

## Invariants for every Section 5 batch

- Preserve the October 9–16, 2027 trip, two-adult/two-child profile and no-park-hopping rule.
- Preserve **Keep / Swap / Wait / Review** decision outputs and user-approved itinerary mutation.
- Do not expose a family key, raw device token, raw invite token, token hash or pepper in source, logs, issues, CI output or long-lived UI.
- Do not change dependency/runtime versions or lockfiles as incidental migration work.
- Do not delete or destructively alter shared-plan, history, account or device data.
- Keep changes incremental, reversible and separately approved with **Start** / **Finalize** checkpoints.
- Do not pull Section 6 production-wide smoke testing or Section 8 product development into Section 5.

# Accounts phase authorization gates

This file defines when explicit user authorization is required during the Accounts, Invitations and Device Management phase.

The default rule is conservative: if a change affects production data, production routes, visible GUI, or the legacy family-key workflow, stop and ask for explicit authorization first.

## Gate 0: safe planning and pure helpers

Allowed without extra authorization after the user asks to continue the phase:

- design documents
- pure helper modules
- unit tests
- CI compile-list updates
- issue comments and phase notes

Not allowed in this gate:

- production database schema changes
- new production routes
- frontend clients that call new routes
- GUI changes
- any change that disables or weakens the existing family key

Current status: completed. The design document and pure token/role helper functions are in place.

## Gate 1: additive production schema setup

Ask for explicit authorization before implementing or merging anything that causes production to create new tables, indexes, extensions, columns, or seed rows.

Authorization wording should be clear, for example:

> Authorize additive account/device schema setup. Keep the current family key working. Do not add routes, frontend code, GUI, or family-key removal.

Allowed only after authorization:

- `CREATE TABLE IF NOT EXISTS` statements for families, members, devices, and invites
- indexes for safe lookup
- seed row for the existing `family` workspace
- seed placeholder owner only if it does not expose or change existing access
- tests proving the existing shared plan, history, restore, and operations endpoints still work

Still not allowed after Gate 1 authorization:

- new account/device API routes
- frontend clients
- visible GUI
- disabling or removing the family key

Rollback expectation:

- No existing table may be altered destructively.
- No existing shared-plan or history row may be modified.
- If there is a deployment problem, the app should still work through the legacy family key.

## Gate 2: production device and invite routes

Ask for explicit authorization only after Gate 1 is deployed and verified.

Authorization wording should be clear, for example:

> Authorize backend device/invite routes. Keep current family-key access enabled. No frontend GUI yet.

Allowed only after authorization:

- list devices
- create invite
- accept invite
- rename device
- revoke device
- dual authorization that accepts either the legacy family key or valid device token

Required tests:

- legacy family key still works
- owner/editor/viewer permissions are enforced
- viewer cannot write or restore
- revoked device cannot read or write
- raw tokens and token hashes never appear in normal list responses
- invite token and device token are only returned once during creation/acceptance

Still not allowed after Gate 2 authorization:

- visible GUI
- family-key removal
- automatic polling
- SMS/text delivery

## Gate 3: frontend typed clients without GUI

Ask for explicit authorization after backend routes pass and deploy.

Authorization wording should be clear, for example:

> Authorize frontend typed clients for device/invite routes. Do not add visible GUI yet.

Allowed only after authorization:

- same-origin Vercel proxy actions for device/invite routes
- typed frontend client functions
- parser and error-handling tests

Still not allowed after Gate 3 authorization:

- visible device-management GUI
- family-key removal
- automatic polling

## Gate 4: minimal device-management GUI

Ask for explicit authorization after typed clients are ready.

Authorization wording should be clear, for example:

> Authorize minimal Shared Family Plan device-management GUI. Do not redesign the whole app.

Allowed only after authorization:

- small device-management section under Shared Family Plan
- manual refresh only
- display connected device names, roles, status, last seen, and revoke controls
- invite creation flow that displays a token or copyable invite only at creation time

GUI limits:

- no app-wide redesign
- no Sexy Edition migration
- no unrelated navigation changes
- no automatic polling unless separately approved

## Gate 5: family-key retirement option

This is not allowed until much later.

Ask for explicit authorization only after all of the following are true:

- at least one active owner device exists
- device login and revocation are verified in production
- a recovery path is documented
- a rollback plan is documented
- the user has manually tested access from the owner device

Authorization wording should be clear, for example:

> Authorize adding an option to disable legacy family-key access. Do not disable it by default.

Important: the first implementation should add only an owner-controlled option. It should not automatically remove or disable the family key.

## Recommendation for the current next authorization

The next risky gate is Gate 1: additive production schema setup.

Before that gate, the assistant should summarize exactly which tables and indexes will be created and ask the user to authorize it explicitly. A generic instruction like "continue" should not be treated as permission to change production schema.

# CastleWatch Dependency Upgrade Policy

_Last established during Rebaseline & Stabilization Section 3D, August 2026._

This file defines how CastleWatch dependency and runtime upgrades are handled after the Section 3 stabilization baseline. The goal is predictable, reversible upgrades without allowing package or runtime drift to become an unreviewed product change.

## Current principle

CastleWatch uses a **known-good pinned baseline**.

- Backend direct Python dependencies are exact-pinned in `requirements.txt`.
- Backend Python is pinned in `.python-version` and CI uses the same interpreter.
- Frontend direct npm dependencies are exact-pinned in `package.json`.
- Frontend `package-lock.json` is committed and CI installs with `npm ci`.
- Frontend Node support is declared as `22.x` and CI uses Node 22.
- Dependency upgrades are separate reviewable changes; they are not bundled into unrelated feature work.

The captured reference versions are recorded in `DEPENDENCY_BASELINE.md`.

## Upgrade rules

1. **Do not use floating dependency declarations.** Do not replace exact direct pins with `latest`, caret (`^`) ranges, tilde (`~`) ranges, or unconstrained runtime versions unless a future architecture decision explicitly changes this policy.
2. **Do not opportunistically upgrade during unrelated work.** Feature, bug-fix, security, migration, and dependency changes should remain separable unless the dependency change is strictly required for the task.
3. **Prefer one logical dependency group per pull request.** A tightly coupled stack may move together when required (for example Next.js with its matching `eslint-config-next`, or React with React DOM). Avoid broad all-package upgrades.
4. **Treat major-version changes as architecture work.** Major upgrades require an explicit compatibility review of CastleWatch application code, CI, Railway/Vercel runtime support, and rollback path before merge.
5. **Security updates may be expedited, not untested.** A security advisory can justify a faster upgrade, but the normal test/build/deployment gates still apply unless an emergency incident requires an explicitly documented exception.
6. **Runtime upgrades are dependency changes.** Python or Node major/minor runtime changes must be reviewed with the same care as library upgrades and must keep production and CI aligned.
7. **Never auto-merge dependency updates.** Automated tooling may surface available updates in the future, but CastleWatch should not automatically merge or deploy them without the normal review gates.

## Backend upgrade procedure

For changes in `MileHighHoosier/castlewatch-2027`:

1. Create an isolated dependency-upgrade branch/PR.
2. Identify the exact target version and why the upgrade is needed.
3. Update only the intended direct pin(s) in `requirements.txt`.
4. If Python itself changes, update `.python-version`, the GitHub Actions interpreter, and the dependency-policy test together.
5. Update the dependency-policy regression test when a deliberate known-good pin changes.
6. Install from `requirements.txt` in a clean environment.
7. Run the full backend contract suite.
8. Compile the production entry modules.
9. Review the diff for unrelated application changes and secrets.
10. After approval, deploy to Railway and verify the deployment status. Request targeted production/iPhone verification when the dependency can plausibly alter runtime behavior.

If the upgrade fails a gate, revert the dependency change rather than weakening the gate to make the upgrade pass.

## Frontend upgrade procedure

For changes in `MileHighHoosier/castlewatch-frontend`:

1. Create an isolated dependency-upgrade branch/PR.
2. Identify the exact target version and why the upgrade is needed.
3. Update the intended exact version(s) in `package.json`.
4. Regenerate/synchronize `package-lock.json` from the intended manifest change and inspect the lockfile diff. Reject unexpected transitive movement when it is not required by the intended upgrade.
5. Keep the package manifest and lockfile exact-version metadata aligned.
6. If Node changes, update `engines.node`, GitHub Actions, and the dependency-policy test together after verifying Vercel supports the target runtime.
7. Run `npm ci` from the committed lockfile.
8. Run the full frontend test suite.
9. Run the production Next.js build.
10. Confirm the actual `castlewatch-frontend` Vercel preview is Ready; do not confuse the known legacy `castlewatch-2027` Vercel project with the production frontend.
11. After approval, merge and verify the production `castlewatch-frontend` Vercel deployment. Request targeted mobile verification when runtime behavior can plausibly change.

If ordinary `npm install` changes unrelated dependencies or lockfile sections, inspect and reduce the change before review instead of accepting an unexplained lockfile churn.

## Compatibility review checklist

Before approving a dependency/runtime upgrade, check the areas the change can affect:

- application framework/runtime compatibility,
- API/request behavior,
- database drivers and PostgreSQL behavior,
- CORS/security middleware,
- build tooling and TypeScript/ESLint compatibility,
- Vercel/Railway runtime support,
- family sync and account/device authentication paths,
- mobile/browser behavior,
- any deprecation or migration steps required by the new version.

The scope of manual verification should match the dependency risk. A documentation/tooling-only change does not need the same production test as a framework or database-driver upgrade.

## Rollback rule

Dependency changes must remain reversible.

- Keep dependency upgrades in their own PR/merge whenever practical.
- If production behavior regresses, restore the last known-good exact versions and lockfile/runtime configuration first, then investigate the upgrade separately.
- Do not stack additional unrelated fixes on top of an unproven dependency upgrade merely to avoid reverting it.
- The current baseline in `DEPENDENCY_BASELINE.md` is the reference for what was known to work when Section 3 was completed.

## Periodic review

CastleWatch does not need continuous churn simply because newer versions exist. Review dependencies deliberately:

- before a dependency reaches end-of-support,
- when a relevant security advisory appears,
- when Railway/Vercel runtime support requires movement,
- when a needed product feature requires a newer dependency,
- or during a scheduled architecture/maintenance audit.

A review can conclude **no upgrade is needed**. Stability is an acceptable outcome.

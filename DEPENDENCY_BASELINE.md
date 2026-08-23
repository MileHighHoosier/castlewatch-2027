# CastleWatch Dependency Baseline

_Baseline captured August 22, 2026 during Rebaseline & Stabilization Section 3A._

This file records the dependency/runtime state that is already known to build and test successfully. Section 3 should preserve this known-good baseline before considering any upgrades.

## Policy decision for Section 3

CastleWatch will use **exact direct-dependency pins** for the current stabilization baseline.

- Do not opportunistically upgrade dependencies while introducing reproducibility controls.
- Pin the versions that are already proven by the current lockfile/green CI first.
- Keep frontend `package-lock.json` committed and use `npm ci` in CI.
- Backend direct dependencies should be pinned to the exact versions proven by green CI.
- Runtime versions should be made explicit where practical so production does not silently drift away from CI.
- Future dependency upgrades should be separate, reviewable changes with tests/builds before production deployment.

## Backend known-good baseline

Repository: `MileHighHoosier/castlewatch-2027`

The backend CI workflow uses Python 3.12. The green Section 2D PR run resolved CPython 3.12.14 and successfully ran the full backend test suite and production-module compilation with these direct dependencies:

| Direct dependency | Known-good version |
| --- | --- |
| Flask | 3.1.3 |
| Gunicorn | 26.1.0 |
| psycopg2-binary | 2.9.12 |
| SQLAlchemy | 2.0.52 |
| requests | 2.34.2 |
| flask-cors | 6.0.5 |

Current `requirements.txt` does **not** pin these versions yet. Section 3B will convert the direct dependency list to exact pins and add a regression/reproducibility check without changing application behavior.

### Backend runtime status

- CI runtime family: Python 3.12.
- Exact green CI interpreter observed: CPython 3.12.14.
- No repository-level production Python version pin was found during 3A.
- Railway may therefore select a compatible/default Python runtime independently of CI unless deployment configuration outside the repository pins it.

Section 3B should make the supported Python runtime explicit in source/deployment configuration after verifying the production-compatible mechanism.

## Frontend known-good baseline

Repository: `MileHighHoosier/castlewatch-frontend`

The committed npm lockfile currently resolves these direct dependencies:

| Direct dependency | Known-good lockfile version |
| --- | --- |
| next | 16.2.6 |
| react | 19.2.6 |
| react-dom | 19.2.6 |
| lucide-react | 1.16.0 |
| typescript | 6.0.3 |
| @types/node | 25.9.1 |
| @types/react | 19.2.15 |
| @types/react-dom | 19.2.3 |
| eslint | 9.39.4 |
| eslint-config-next | 16.2.6 |

Current `package.json` declares all of these as `latest`, even though `package-lock.json` resolves exact versions. This means `npm ci` is deterministic today, but future lockfile regeneration or ordinary `npm install` can move the direct dependencies unexpectedly.

Section 3C will replace the `latest` declarations with the exact versions above, synchronize the lockfile, and preserve deterministic `npm ci` behavior.

### Frontend runtime status

- CI explicitly uses Node.js 22.
- CI installs with `npm ci`, then runs tests and a production Next.js build.
- `package.json` currently has no `engines.node` constraint.
- No repository-level `.nvmrc` or equivalent Node runtime pin was found during 3A.
- The Vercel production runtime may therefore be controlled by Vercel project settings/defaults rather than repository source.

Section 3C should make the supported Node runtime explicit in the repository after verifying compatibility with the actual Vercel build environment.

## What 3A does not do

3A is inventory and policy only. It does not:

- change any package version,
- regenerate a lockfile,
- alter Railway/Vercel runtime settings,
- change application behavior,
- retire the family key,
- change account/device authorization,
- introduce dependency upgrades.

## Next actions

1. **3B — Backend dependency controls:** exact-pin the six proven direct Python dependencies and make the supported Python runtime explicit using the deployment mechanism verified for Railway.
2. **3C — Frontend dependency controls:** replace `latest` with the lockfile-proven direct versions, keep `package-lock.json` synchronized, and make the Node runtime expectation explicit.
3. **3D — Upgrade procedure and full QC:** document the upgrade workflow, run full backend/frontend tests and production builds, and only then consider Section 3 complete.

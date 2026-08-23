# CastleWatch Dependency Baseline

_Baseline captured August 22, 2026 during Rebaseline & Stabilization Section 3A and reconciled through Section 3C._

This file records the exact dependency/runtime state proven during Section 3. It is the rollback/reference baseline for future dependency work. The upgrade procedure is defined in `DEPENDENCY_POLICY.md`.

## Baseline policy

CastleWatch uses **exact direct-dependency pins** for the stabilization baseline.

- Backend direct Python dependencies are exact-pinned in `requirements.txt`.
- Backend Python is pinned to 3.12.14 in `.python-version`, and CI uses the same interpreter.
- Frontend direct npm dependencies are exact-pinned in `package.json`.
- Frontend `package-lock.json` is committed and CI installs with `npm ci`.
- Frontend declares Node `22.x`, and CI uses Node 22.
- Dependency upgrades are separate, reviewable changes with tests/builds before production deployment.

## Backend known-good baseline

Repository: `MileHighHoosier/castlewatch-2027`

| Direct dependency | Known-good version |
| --- | --- |
| Flask | 3.1.3 |
| Gunicorn | 26.1.0 |
| psycopg2-binary | 2.9.12 |
| SQLAlchemy | 2.0.52 |
| requests | 2.34.2 |
| flask-cors | 6.0.5 |

Runtime/control state:

- Python: **3.12.14**.
- `.python-version`: **3.12.14**.
- GitHub Actions: **3.12.14**.
- `requirements.txt`: exact direct pins above.
- `tests/test_dependency_policy.py`: guards the expected dependency/runtime controls.
- Section 3B clean CI successfully installed from the exact pins, ran the full backend test suite, and compiled production modules.
- The merged 3B Railway deployment completed successfully.

## Frontend known-good baseline

Repository: `MileHighHoosier/castlewatch-frontend`

| Direct dependency | Known-good version |
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

Runtime/control state:

- Node: **22.x** declared in `package.json`.
- GitHub Actions: **Node 22**.
- CI install command: **`npm ci`**.
- `package-lock.json`: committed and synchronized to the exact direct pins.
- `tests/dependencyPolicy.test.mjs`: guards manifest/lockfile/runtime/CI alignment.
- Section 3C clean CI successfully ran `npm ci`, the full frontend tests, and the production Next.js build.
- The actual `castlewatch-frontend` Vercel preview and merged production deployment completed successfully.
- The separate legacy `castlewatch-2027` Vercel project is not the production frontend and may continue to report an unrelated error until later deployment-hygiene cleanup.

## Section 3 history

- **3A:** captured the known-good dependency/runtime baseline and selected exact direct pins as the stabilization strategy.
- **3B:** implemented backend exact pins and Python runtime alignment with regression protection.
- **3C:** replaced frontend `latest` declarations with exact known-good versions, synchronized the lockfile, declared Node 22.x, and added regression protection.
- **3D:** establishes the long-term upgrade/rollback procedure and performs the final cross-repository QC pass before Section 3 is closed.

## Rollback reference

If a future dependency/runtime upgrade causes a production regression and no data/schema migration prevents rollback, restore the exact versions/runtime controls in this file first, then investigate the upgrade separately. Do not normalize a broken upgrade by weakening tests or stacking unrelated fixes onto it.

# CastleWatch Agent Instructions

Read these instructions before modifying this repository.

## Required context

CastleWatch spans two repositories:

- backend: `MileHighHoosier/castlewatch-2027`
- frontend: `MileHighHoosier/castlewatch-frontend`

Before cross-cutting or architectural changes, inspect both repositories and read:

- `PROJECT_STATE.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `DEPENDENCY_POLICY.md` before any dependency/runtime change
- `DEPENDENCY_BASELINE.md` when evaluating or rolling back dependency/runtime changes

Do not rely on old chat history as the source of truth when repository documentation and code disagree.

## Production-path discipline

The Railway production path is:

`railpack.json -> gunicorn api_server:app -> api_server.py -> app.py -> core_app.py`

Trace imports/routes before changing older scaffold code.

Legacy-looking areas such as `bots/`, `scheduler/`, `collectors/`, `ai_engine/`, and old `README_FILEPACK*.txt` material may not be part of the current production system. In particular, `bots/waitdragon.py` contains simulated/random waits and must never be substituted for the live Queue Times collector in `core_app.py`.

## Change rules

1. Preserve user-visible behavior unless the task explicitly requires a change or a change is necessary for security/reliability.
2. Prefer incremental, reversible patches over broad rewrites.
3. Add or update automated tests for behavioral changes.
4. Preserve graceful degradation when external sources fail.
5. Do not silently alter the October 9-16, 2027 trip assumptions; flag itinerary/config changes explicitly.
6. Itinerary changes must remain user-approved rather than automatic.
7. Do not describe historical wait forecasts as precise 2027 predictions.
8. Keep secrets, family keys, raw device tokens and raw invite tokens out of source control, logs and error output.
9. Do not return internal exception details to clients when a generic error can be used.
10. Update project documentation when a change alters architecture, roadmap status or the authoritative project state.
11. Keep dependency/runtime changes isolated and follow `DEPENDENCY_POLICY.md`; do not reintroduce floating direct dependency ranges or bundle opportunistic upgrades into unrelated work.

## Account/device migration safety gate

The Accounts / Invitations / Device Management migration is complete and production-verified through Section 5. Family-key recovery remains an intentional safety boundary.

- Do **not** remove or disable `CASTLEWATCH_FAMILY_KEY`.
- Keep credential selection explicit and reject a missing, invalid or revoked selected credential without silent fallback.
- Preserve the server-enforced Owner/Editor/Viewer matrix and family-key recovery behavior for normal shared-plan operations.
- Do **not** implement legacy-key retirement without a separate explicit user approval.

## Forecasting rule

Current forecasting is historical directional intelligence based mainly on stored wait observations, same-weekday evidence and time blocks. Seasonality, holidays/events, recent trends, operating-hours normalization and cross-park effects are not fully modeled yet.

Any UI/API copy or recommendation logic must respect that limitation.

## Data-source boundaries

- Live attraction waits: Queue Times through `core_app.py`.
- Weather alerts: weather.gov.
- Historical waits/forecast evidence: Railway PostgreSQL `wait_times`.
- Trip Week/event intelligence: backend Trip Week/calendar/event modules.
- Shared family trip: PostgreSQL current document + version history.

Verify source provenance before adding a new source or changing fallback behavior.

## Before finalizing a change

- run the relevant tests,
- compile/build affected production code when applicable,
- verify no secret/token was added to source or output,
- for dependency/runtime changes, verify the exact pin/runtime/rollback requirements in `DEPENDENCY_POLICY.md`,
- check whether the frontend repository needs a coordinated change,
- update `PROJECT_STATE.md`, `ARCHITECTURE.md` or `ROADMAP.md` when status/boundaries changed.

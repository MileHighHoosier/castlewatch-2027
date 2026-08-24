# CastleWatch Architecture

_Last rebaseline: August 2026_

## System overview

CastleWatch is split across two GitHub repositories and two production services:

```text
iPhone / browser
      |
      v
Vercel - Next.js frontend
MileHighHoosier/castlewatch-frontend
      |
      | HTTPS JSON API
      v
Railway - Flask backend
MileHighHoosier/castlewatch-2027
      |
      v
Railway PostgreSQL
```

The frontend owns user interaction and a significant amount of planning logic. The backend owns live-data collection, historical persistence/analysis, Trip Week source data, calendar/event intelligence, shared family storage, account/device authorization, and operations endpoints.

## Repositories

### Backend: `MileHighHoosier/castlewatch-2027`

Production entry path:

```text
railpack.json
  -> gunicorn api_server:app
      -> api_server.py
          -> app.py
              -> core_app.py
```

`core_app.py` contains the original Flask application and live park APIs. `app.py` wraps that app and registers shared-family/account routes. `api_server.py` is the Railway Gunicorn entrypoint and applies family-mode attraction exclusions.

Important backend modules include:

- `core_app.py` - live ride collection/reads, historical planning insights, weather advisory endpoint, Trip Week route registration.
- `tomorrow_forecast.py` - historical same-weekday/time-block forecasting.
- `trip_week.py` - October 2027 base itinerary, alternate scenario and attached forecast/event intelligence.
- `calendar_ingestion.py` - calendar-source refresh/cache flow.
- `special_events.py` - event/holiday intelligence and scenario signals.
- `family_trip.py` - shared family-trip document, optimistic versions, history and restore.
- `operations.py` - shared-trip operations/usage reporting.
- `accounts_auth.py` - token generation, parsing, hashing and role helpers.
- `accounts_access.py` - family-key/device-token authorization helpers.
- `accounts_schema.py` - family/member/device/invite schema setup.
- `accounts_routes.py` - device/invite management endpoints.

### Frontend: `MileHighHoosier/castlewatch-frontend`

Production entry path:

```text
app/page.tsx
  -> DashboardShell
      -> park command center / Trip Week / Getting There
```

Important frontend areas include:

- `app/components/ParkCommandCenter.tsx` - live park dashboard, ride/heat/activity/plan experience.
- `app/components/TripWeekPlanner.tsx` - trip-week rendering, resort editing, reservations and scenario controls.
- `app/components/TripWeekDecisionPanel.tsx` - assembles browser-local trip inputs and renders decision/support panels.
- `app/lib/tripDecisionEngine.ts` - base-vs-alternate scenario scoring and recommendation logic.
- `app/lib/tripProfile.ts` - trip profile, reservation model, leave-by guidance.
- `app/lib/tripResorts.ts` - overnight resort plan/options.
- `app/lib/tripWeekApproval.ts` - scenario approval/lock state.
- `app/components/TransportationPlanner.tsx` - Getting There guidance and route calculations.
- `app/components/WeatherAwarePlanning.tsx` - weather risk mode and automatic weather advisory integration.
- Lightning Lane / emergency / show / activity / character components - active park-day support layers.
- `app/lib/familyTripSync.ts` - browser-local/shared plan synchronization model.
- `app/lib/familyTripDevices.ts` - device credential storage and typed device/invite models.
- `app/api/*` - Next.js proxy routes between browser UI and Railway protected endpoints.

The pre-existing unlinked `app/sexy` route is an experimental presentation concept, not the documented core production entry path. Section 4F left it unchanged; any future removal, archival or promotion should be an explicit cleanup/product decision rather than an incidental stabilization edit.

## Live attraction data flow

Current production live ride collection uses Queue Times, not the old scaffold bots.

```text
Queue Times
   |
   v
core_app.collect_wait_times()
   |
   v
PostgreSQL wait_times
   |
   +--> /api/rides
   +--> /api/planning-insights
   +--> tomorrow_forecast.py / Trip Week historical signals
```

The backend filters character meets and non-ride experiences from the ride-priority data set.

### Legacy warning

Files under older scaffold areas such as `bots/`, `scheduler/`, `collectors/`, `ai_engine/`, and old `README_FILEPACK*.txt` material may not represent the production path. In particular, `bots/waitdragon.py` produces random simulated waits and must never be treated as the live production collector.

Before changing a legacy-looking subsystem, trace whether it is imported by the current Railway entry path.

## Historical forecast model

`tomorrow_forecast.py` groups stored wait observations into Walt Disney World local-time blocks:

- morning,
- midday,
- afternoon,
- evening.

For a target date it prefers same-weekday history when sufficient evidence exists, otherwise falls back to an overall park baseline. It reports sample count, distinct days, relative comparison, best historical window, peak window and evidence-volume confidence.

This is **historical directional intelligence**, not a precise future crowd prediction. It does not yet fully model seasonality, holidays, recent trends, park-hours normalization or cross-park displacement.

## Trip Week and event intelligence

`trip_week.py` currently owns the October 9-16, 2027 base itinerary and a specific Magic Kingdom/Epcot alternate scenario.

The backend attaches:

- historical date forecasts,
- special-event/calendar signals,
- provisional behavior when official 2027 schedules are unavailable.

The frontend then combines those backend signals with browser-local inputs in `tripDecisionEngine.ts`:

- reservations,
- no-park-hopping preference,
- overnight resorts,
- transportation convenience heuristics,
- historical forecast risk,
- event risk.

The final scenario change remains user-approved; CastleWatch must not silently rearrange the trip.

## Weather data flow

```text
weather.gov active alerts
       |
       v
core_app.get_weather_advisory()
       |
       v
/api/weather-advisory
       |
       v
WeatherAwarePlanning frontend
```

Weather currently influences park-day presentation and safe-mode behavior. Long-range weather is intentionally not treated as dependable Trip Week evidence far in advance.

A known rebaseline issue is that a failed weather refresh can clear a prior automatic warning; stabilization work should preserve last-known warnings and mark them stale instead.

## Browser-local state

Several user-editable planning features currently use `localStorage`, including:

- trip profile,
- reservations,
- resort plan,
- Trip Week scenario approval,
- Lightning Lane windows,
- weather mode/override state,
- family sync metadata,
- legacy family key,
- device token metadata/credential.

The newer shared-family system synchronizes selected trip state to PostgreSQL, but browser-local state remains important to the current UI.

### Frontend state architecture caution

Some older/rapidly-added UI layers modify the DOM imperatively, inject styles, poll `localStorage`, or attach global handlers instead of using a single declarative React state model. Stabilization should improve this incrementally rather than performing an uncontrolled rewrite.

## Shared family trip data model

The shared trip uses one logical family document (`family`) in PostgreSQL.

Core tables:

- `family_trip_state` - current payload/version.
- `family_trip_history` - retained historical versions.

Write model:

1. client reads current version,
2. client submits `expectedVersion`,
3. backend takes a PostgreSQL advisory/write lock,
4. backend rejects stale writes with HTTP 409,
5. successful write creates the next version,
6. a history snapshot is inserted,
7. history is pruned to the most recent 25 versions.

Restore creates a **new current version** from an older snapshot rather than rewriting history.

## Account/device authorization architecture

Additive account tables:

- `castlewatch_families`,
- `castlewatch_members`,
- `castlewatch_devices`,
- `castlewatch_invites`.

Token model:

- device tokens use a `cwdev_<lookup>_<secret>` form,
- invite tokens use a `cwinv_<lookup>_<secret>` form,
- raw secrets are intended to be shown only at creation/acceptance time,
- hashes are stored server-side using HMAC-SHA256 with a server pepper,
- role helpers support owner/editor/viewer semantics.

### Migration boundary

The migration is incomplete.

The device-management API can authorize device tokens, but normal shared-plan proxy actions still depend on the legacy family key in important paths. Do not infer from the existence of device tables/UI that the family-key migration is complete.

`CASTLEWATCH_FAMILY_KEY` remains required for recovery and current shared-plan behavior until the migration's acceptance gates are explicitly satisfied.

The authoritative remaining-work boundary is `docs/accounts_migration_contract.md`. Section 5A confirmed that no product route currently creates an owner device, normal shared-plan/history/restore/operations actions remain family-key-only, browser credential selection can mask device-only state, `legacy_family_key_enabled` is not yet an authoritative production gate, and raw device credentials still live in JavaScript-readable `localStorage`.

Before device credentials gain normal shared-plan authority, the protected Vercel proxy must move the raw token into a narrowly scoped `Secure`, `HttpOnly`, `SameSite=Strict` cookie, retain strict same-origin request validation, and select exactly one credential without silently falling back from a rejected/revoked device to the family key. This is the planned Section 5B boundary, not current deployed behavior. Owner bootstrap must remain an explicit family-key recovery action and must not disable the legacy-key flag.

## Frontend/backend proxy boundary

The browser uses Next.js API routes for protected family operations so Vercel can proxy requests to Railway. The main proxy is `app/api/castlewatch-family-sync/route.ts`.

During stabilization, authorization behavior should be kept consistent across:

1. browser credential selection,
2. Next.js proxy validation/headers,
3. Flask endpoint authorization,
4. role enforcement in database operations.

Changing only one layer can create misleading "connected" states.

## Deployment

### Frontend

- Host: Vercel.
- Framework: Next.js.
- Backend base URL is configured with the `NEXT_PUBLIC_API_BASE_URL` compatibility path currently used by the project.

### Backend

- Host: Railway.
- Start command: `gunicorn api_server:app --bind 0.0.0.0:$PORT`.
- PostgreSQL provided by Railway.

At the Section 4 closeout, both merged repository heads deployed successfully to Railway and the real `castlewatch-frontend` Vercel project. Deployment success still does not replace functional production verification.

## Automated checks

### Backend

GitHub Actions uses Python 3.12.14, installs the exact pinned requirements, runs all 69 backend contracts and compiles every active root production module. Coverage includes account authorization/routes, invite atomicity, shared family storage/history/operations, ride read/refresh safety, response/CORS security, dependency/deployment controls, weather safety, live planning insights, historical/date forecasting, calendar/event intelligence and Trip Week attachment/fallback behavior.

### Frontend

GitHub Actions uses Node 22 with clean `npm ci`, runs all 82 frontend contracts, builds the production Next.js application and executes the dependency-free 390×844 Chrome smoke. Coverage includes dependency controls, credential/device safety, shared sync/history/operations, weather, Trip Week decisions, transportation/reservations, Lightning Lane, Park Command Center, Live Plan, emergency mode, shows/activities/characters and the key mobile navigation flow.

Section 4 materially broadened core regression protection. Production functional smoke verification and contracts for future Section 5+ behavior remain separate roadmap work.

## Architecture rules for future work

1. Inspect **both repositories** before cross-cutting changes.
2. Treat `PROJECT_STATE.md` and this file as the current architectural baseline after they are merged.
3. Trace the real production import/render path before editing legacy scaffold files.
4. Preserve user approval for itinerary/schedule changes.
5. Preserve graceful degradation when external data is unavailable.
6. Never present historical forecasts as precise future predictions.
7. Do not retire the family key until the documented migration gates are satisfied.
8. Prefer incremental, reversible changes with tests over broad rewrites.
9. Keep secrets and raw device/invite tokens out of source control, logs and long-lived UI output.
10. Update this architecture document when a change alters a system boundary or source of truth.

# CastleWatch 2027 Backend

CastleWatch is a private-family Walt Disney World planning and trip-operations system for the October 9-16, 2027 trip.

This repository contains the **Flask/Python backend deployed on Railway** and its Railway PostgreSQL data layer. The companion Next.js frontend is [`MileHighHoosier/castlewatch-frontend`](https://github.com/MileHighHoosier/castlewatch-frontend) and is deployed on Vercel.

CastleWatch is an unofficial personal planning tool and is not affiliated with Disney.

## Start here

Current cross-repository documentation:

- [`PROJECT_STATE.md`](PROJECT_STATE.md) - what is complete, partial, unfinished and currently next.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - production paths, data flows, state boundaries and account-migration constraints.
- [`ROADMAP.md`](ROADMAP.md) - Rebaseline & Stabilization sequence and later product phases.
- [`AGENTS.md`](AGENTS.md) - instructions and safety gates for future coding agents.

These files supersede old chat-only progress estimates after they are reviewed and merged.

## Production path

Railway starts:

```text
gunicorn api_server:app
```

which resolves through:

```text
api_server.py
  -> app.py
      -> core_app.py
```

Do not assume older `bots/`, `scheduler/`, `collectors/`, `ai_engine/` or `README_FILEPACK*.txt` scaffold material is part of the live production path. Trace imports before changing it.

## Current backend responsibilities

- Queue Times ride collection and latest ride reads.
- Historical wait storage and planning insights.
- Historical same-weekday/time-of-day forecast signals.
- weather.gov alert ingestion.
- October 2027 Trip Week data and alternate scenario.
- calendar/special-event intelligence.
- shared family-trip PostgreSQL document, versions and restore.
- operations/usage support.
- account/device/invite schema and authorization foundations.

## Current development phase

**Rebaseline & Stabilization**

Do not begin a major new feature from this repository without checking `PROJECT_STATE.md` and `ROADMAP.md` first.

The Accounts / Invitations / Device Management migration is incomplete. In particular, do **not** remove or disable `CASTLEWATCH_FAMILY_KEY` or assume device tokens have replaced the family key for all shared-plan operations.

## Tests

Backend GitHub Actions currently runs:

```bash
python -m unittest discover -s tests -v
```

and compiles key production modules.

Regression coverage is strongest around the newer shared-family/account work and still needs expansion across older park-planning features.

## Deployment

- Backend: Railway.
- Database: Railway PostgreSQL.
- Frontend: Vercel, from the companion repository.

Deployment success is not a substitute for production functional verification.
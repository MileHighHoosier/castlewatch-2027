# CastleWatch Project Tracker

_Canonical cross-repository tracker · audited August 31, 2026_

## Fresh-agent handoff

- **Current phase:** Section 7 tracker implementation and checklist are in review; Sections 1–6 are complete and production-verified.
- **Current blocker:** the implementation checkpoint must merge before the separately commanded Section 7 Finalize checkpoint.
- **Exact next command after this checkpoint merges:** `Finalize Section 7`.
- **Governing sources:** [PROJECT_STATE.md](PROJECT_STATE.md), [ROADMAP.md](ROADMAP.md), [Section 7 contract](docs/section-7-project-tracker.md), and backend issue [#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61).
- **Repository snapshot:** backend `78926483a8509825703ec093dadee8d257301259`; frontend `90fa1f5eb3d2803e728ce7fcf067fd6f8edd6c0f`.

This is the one version-controlled work tracker for CastleWatch. GitHub issues and pull requests remain authoritative implementation evidence. `PROJECT_STATE.md` remains authoritative product state, and `ROADMAP.md` remains authoritative phase order.

## Vocabulary

Status values:

- `IN_PROGRESS` — approved work is actively executing.
- `NOT_STARTED` — scoped work has not begun.
- `BLOCKED` — a named dependency must finish first.
- `NEEDS_DECISION` — the user must choose scope or disposition.
- `DEFERRED` — intentionally postponed with an explicit reason and next review action.

QC status values:

- `NOT_RUN` — acceptance checks have not begun.
- `IN_REVIEW` — implementation exists and checklist evidence is being reviewed.
- `PASSED` — the task's documented acceptance and QC checks passed.
- `NOT_APPLICABLE` — no executable QC applies until a decision is made.

## Active and future work

| ID | Phase | Task | Status | Owner/agent | Acceptance criteria | Dependencies | QC status | GitHub | Last update | Exact next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CW-001 | Section 7 | Implement the canonical project tracker | IN_PROGRESS | Codex | Both repositories reconciled; required fields populated; validator and tests pass; handoff is recoverable | None | IN_REVIEW | [backend#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61) | 2026-08-31 | Merge the Section 7 implementation checkpoint and record its evidence in backend issue #61. |
| CW-002 | Section 7 | Finalize Section 7 | BLOCKED | User + Codex | Implementation is merged; issue checklist is complete; state and roadmap record closeout | CW-001 | NOT_RUN | [backend#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61) | 2026-08-31 | After CW-001 merges, run `Finalize Section 7`. |
| CW-003 | Operations follow-up | Decide disposition of browser-local usage counters | NEEDS_DECISION | User | Choose whether frontend issue #14 is superseded by Operations v1 or belongs in later operations work | None | NOT_APPLICABLE | [frontend#14](https://github.com/MileHighHoosier/castlewatch-frontend/issues/14), [backend#7](https://github.com/MileHighHoosier/castlewatch-2027/issues/7) | 2026-08-31 | Decide whether to close frontend #14 as superseded or schedule it as later operations work. |
| CW-004 | Section 8 | Start Trip Week Phase 2 unified recommendation engine | BLOCKED | User + Codex | Section 8 receives its own approved Start checkpoint with bounded acceptance criteria | CW-002 | NOT_RUN | [ROADMAP](ROADMAP.md#section-8---resume-product-development) | 2026-08-31 | After CW-002 passes, run `Start Section 8`. |
| CW-005 | Stabilization | Harden ride-refresh authorization and interface | NOT_STARTED | Unassigned | Public compatibility GET is replaced or protected without breaking bounded refresh safety | CW-002 | NOT_RUN | [PROJECT_STATE](PROJECT_STATE.md#known-rebaseline-findings-still-requiring-remediation) | 2026-08-31 | After Section 7 closes, open a bounded design issue when the user prioritizes this high-risk item. |
| CW-006 | Stabilization | Reduce remaining dynamic HTML and imperative frontend state debt | NOT_STARTED | Unassigned | Remaining sinks and polling/DOM patches are audited and split into regression-backed repair issues | CW-002 | NOT_RUN | [PROJECT_STATE](PROJECT_STATE.md#known-rebaseline-findings-still-requiring-remediation) | 2026-08-31 | Audit the remaining frontend sinks and state patches, then propose small repair issues. |
| CW-007 | Maintenance | Archive or remove legacy scaffold code | NOT_STARTED | Unassigned | Unused scaffold paths are proven unreachable and removed or clearly archived without behavior change | CW-002 | NOT_RUN | [PROJECT_STATE](PROJECT_STATE.md#known-rebaseline-findings-still-requiring-remediation) | 2026-08-31 | Inventory legacy paths and produce a deletion-safe dependency map. |
| CW-008 | Maintenance | Clean up legacy Flask-CORS initialization | NOT_STARTED | Unassigned | Global legacy initialization is removed or narrowed while current origin policy remains regression-protected | CW-002 | NOT_RUN | [PROJECT_STATE](PROJECT_STATE.md#known-rebaseline-findings-still-requiring-remediation) | 2026-08-31 | Open a focused backend cleanup issue with current CORS tests as acceptance gates. |
| CW-009 | Maintenance | Remove obsolete Vercel project integration | NOT_STARTED | User + Codex | Obsolete project linkage is identified and removed without touching the authoritative frontend deployment | CW-002 | NOT_RUN | [PROJECT_STATE](PROJECT_STATE.md#known-rebaseline-findings-still-requiring-remediation) | 2026-08-31 | Confirm the obsolete project identifier before any hosting configuration change. |
| CW-010 | Privacy | Decide repository privacy and configuration separation | NEEDS_DECISION | User | Decide whether public repositories may retain personal trip dates and itinerary defaults | None | NOT_APPLICABLE | [PROJECT_STATE](PROJECT_STATE.md#known-rebaseline-findings-still-requiring-remediation) | 2026-08-31 | Choose private repositories, configuration separation, or explicit acceptance of the current exposure. |
| CW-011 | Product roadmap | Reservation Awareness Phase 2 and 60-day planner | NOT_STARTED | Unassigned | Booking windows, priorities, statuses, reminders and contingency choices are implemented with user-approved scope | CW-004 | NOT_RUN | [ROADMAP](ROADMAP.md#2-reservation-awareness-phase-2--60-day-planner) | 2026-08-31 | After Section 8 starts, define a bounded phase contract and dependency order. |
| CW-012 | Product roadmap | Prediction Phase 2 | NOT_STARTED | Unassigned | Seasonal, event, recent-trend, park-hour and confidence improvements are scoped and regression-tested | CW-004 | NOT_RUN | [ROADMAP](ROADMAP.md#3-prediction-phase-2) | 2026-08-31 | After Section 8 starts, define model inputs, evidence limits and calibration acceptance criteria. |
| CW-013 | Product roadmap | Cross-park ripple prediction | BLOCKED | Unassigned | Displacement from events, weather, outages and schedules is estimated with explainable confidence | CW-012 | NOT_RUN | [ROADMAP](ROADMAP.md#4-cross-park-ripple-prediction) | 2026-08-31 | Complete CW-012 before designing cross-park effects. |
| CW-014 | Product roadmap | Actionable notifications and change alerts | BLOCKED | Unassigned | Alerts are limited to material, actionable changes with explicit delivery and deduplication rules | CW-004, CW-011, CW-012 | NOT_RUN | [ROADMAP](ROADMAP.md#5-notifications-and-change-alerts) | 2026-08-31 | Complete the prerequisite product phases, then rank alert types by user value. |
| CW-015 | Product roadmap | Trip-Day Command Center and mobile polish | BLOCKED | Unassigned | Active-park mobile view is reduced to the smallest reliable trip-day decision surface | CW-004, CW-011 | NOT_RUN | [ROADMAP](ROADMAP.md#6-trip-day-command-center--mobile-polish) | 2026-08-31 | Complete the recommendation and reservation foundations before scoping the trip-day surface. |

## Completed phase summary

| Phase | Result | Evidence |
| --- | --- | --- |
| Sections 1–6 | Complete and production-verified through August 31, 2026 | [PROJECT_STATE](PROJECT_STATE.md#rebaseline-stabilization-status), [ROADMAP](ROADMAP.md), [Section 6 issue #53](https://github.com/MileHighHoosier/castlewatch-2027/issues/53) |

Completed work is summarized here instead of being expanded into active task rows. Individual merged evidence remains in the linked project state, roadmap and GitHub records.

## Maintenance rules

1. **Start:** create or activate one stable `CW-NNN` row, set the owner, acceptance criteria, dependencies, GitHub record, date and exact next action.
2. **Checklist:** update QC status and exact next action as evidence passes; link every discovered defect instead of burying it in prose.
3. **Defect repair:** add or update a stable row, link its issue and PR, and preserve the parent phase dependency.
4. **Finalize:** only move completed work into the summary after merged acceptance/QC evidence exists and any required deployment verification passes.
5. **Decision/defer:** retain a concrete user decision or review action; never use a vague `TBD` next step.
6. **QC:** run `python scripts/validate_project_tracker.py` and the repository test suite after every tracker edit.
7. **Safety:** never record secrets, raw credentials, family keys, token material or private operational payloads.


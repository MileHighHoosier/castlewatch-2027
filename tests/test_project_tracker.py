import unittest
from pathlib import Path

from scripts.validate_project_tracker import validate_tracker_text


TRACKER_PATH = Path(__file__).resolve().parents[1] / "PROJECT_TRACKER.md"


class ProjectTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = TRACKER_PATH.read_text(encoding="utf-8")

    def test_canonical_tracker_is_valid(self):
        self.assertEqual(validate_tracker_text(self.tracker), [])

    def test_duplicate_task_ids_are_rejected(self):
        duplicate = self.tracker.replace(
            "| CW-003 | Operations follow-up |",
            "| CW-005 | Operations follow-up |",
            1,
        )
        self.assertIn("duplicate task ID: CW-005", validate_tracker_text(duplicate))

    def test_invalid_vocabulary_is_rejected(self):
        invalid = self.tracker.replace(
            "| CW-003 | Operations follow-up | Decide disposition of browser-local usage counters | NEEDS_DECISION |",
            "| CW-003 | Operations follow-up | Decide disposition of browser-local usage counters | STARTED |",
            1,
        )
        errors = validate_tracker_text(invalid)
        self.assertTrue(any("invalid status 'STARTED'" in error for error in errors))

    def test_blank_required_field_is_rejected(self):
        invalid = self.tracker.replace(
            "| CW-003 | Operations follow-up |", "| CW-003 |  |", 1
        )
        errors = validate_tracker_text(invalid)
        self.assertIn("CW-003 has blank field 'Phase'", errors)

    def test_handoff_names_current_phase_blocker_and_next_command(self):
        handoff = self.tracker.split("## Vocabulary", 1)[0]
        self.assertIn("Current phase", handoff)
        self.assertIn("Current blocker", handoff)
        self.assertIn("Reservation Awareness Phase 2B (CW-018) is implemented, locally verified, corrected after exact-head review and published for review", handoff)
        self.assertIn("frontend PR [#58]", handoff)
        self.assertIn("documentation PR [#94]", handoff)
        self.assertIn("No merge or deployment is authorized", handoff)
        self.assertIn("documentation PR #94 must pass exact-head backend CI", handoff)
        self.assertIn("Stop on failure; do not merge, deploy or begin Phase 2C implicitly", handoff)

    def test_phase_2a_is_completed_after_cw016_finalization(self):
        self.assertNotIn("| CW-016 | Corrective checkpoint |", self.tracker)
        self.assertIn(
            "| CW-011 | Product roadmap | Reservation Awareness Phase 2 and 60-day planner | IN_PROGRESS |",
            self.tracker,
        )
        self.assertIn(
            "| Pre–Phase 2A corrective checkpoint (CW-016) | Complete, production-verified and finalized September 8, 2026 |",
            self.tracker,
        )
        self.assertNotIn("| CW-017 | Reservation Awareness Phase 2A |", self.tracker.split("## Completed phase summary", 1)[0])
        self.assertIn(
            "| Reservation Awareness Phase 2A (CW-017) | Complete, production-verified and finalized September 8, 2026 |",
            self.tracker,
        )
        self.assertIn("[issue #90](https://github.com/MileHighHoosier/castlewatch-2027/issues/90)", self.tracker)

    def test_phase_2b_is_active_and_bounded(self):
        active = self.tracker.split("## Completed phase summary", 1)[0]
        self.assertIn("| CW-018 | Reservation Awareness Phase 2B |", active)
        self.assertIn("[issue #93](https://github.com/MileHighHoosier/castlewatch-2027/issues/93)", active)
        self.assertIn("[frontend PR #58](https://github.com/MileHighHoosier/castlewatch-frontend/pull/58)", active)
        self.assertIn("[documentation PR #94](https://github.com/MileHighHoosier/castlewatch-2027/pull/94)", active)
        self.assertIn("[checkpoint](docs/reservation-awareness-phase-2b.md)", active)


if __name__ == "__main__":
    unittest.main()

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
        duplicate = self.tracker.replace("| CW-002 |", "| CW-001 |", 1)
        self.assertIn("duplicate task ID: CW-001", validate_tracker_text(duplicate))

    def test_invalid_vocabulary_is_rejected(self):
        invalid = self.tracker.replace("| IN_PROGRESS |", "| STARTED |", 1)
        errors = validate_tracker_text(invalid)
        self.assertTrue(any("invalid status 'STARTED'" in error for error in errors))

    def test_blank_required_field_is_rejected(self):
        invalid = self.tracker.replace(
            "| CW-001 | Section 7 |", "| CW-001 |  |", 1
        )
        errors = validate_tracker_text(invalid)
        self.assertIn("CW-001 has blank field 'Phase'", errors)

    def test_handoff_names_current_phase_blocker_and_next_command(self):
        handoff = self.tracker.split("## Vocabulary", 1)[0]
        self.assertIn("Current phase", handoff)
        self.assertIn("Current blocker", handoff)
        self.assertIn("`Finalize Section 7`", handoff)


if __name__ == "__main__":
    unittest.main()

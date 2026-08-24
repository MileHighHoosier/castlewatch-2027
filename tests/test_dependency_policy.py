from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REQUIREMENTS = [
    "flask==3.1.3",
    "gunicorn==26.1.0",
    "psycopg2-binary==2.9.12",
    "sqlalchemy==2.0.52",
    "requests==2.34.2",
    "flask-cors==6.0.5",
]
EXPECTED_PYTHON = "3.12.14"


class DependencyPolicyTests(unittest.TestCase):
    def test_backend_direct_dependencies_are_exactly_pinned(self):
        lines = [
            line.strip()
            for line in (ROOT / "requirements.txt").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(lines, EXPECTED_REQUIREMENTS)
        for line in lines:
            self.assertIn("==", line)
            self.assertNotIn(">=", line)
            self.assertNotIn("~=", line)

    def test_python_runtime_pin_matches_ci(self):
        runtime = (ROOT / ".python-version").read_text().strip()
        self.assertEqual(runtime, EXPECTED_PYTHON)

        workflow = (
            ROOT / ".github" / "workflows" / "family-sync-tests.yml"
        ).read_text()
        self.assertIn(f'python-version: "{EXPECTED_PYTHON}"', workflow)
        self.assertIn("python -m py_compile *.py", workflow)


if __name__ == "__main__":
    unittest.main()

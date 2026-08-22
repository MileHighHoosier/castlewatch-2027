import json
import pathlib
import shlex
import unittest


class DeploymentConfigTests(unittest.TestCase):
    def test_gunicorn_keeps_read_capacity_during_refresh(self):
        config_path = pathlib.Path(__file__).resolve().parents[1] / "railpack.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        command = config["deploy"]["startCommand"]
        args = shlex.split(command)

        self.assertEqual("gunicorn", args[0])
        self.assertIn("api_server:app", args)

        workers_index = args.index("--workers")
        timeout_index = args.index("--timeout")
        self.assertGreaterEqual(int(args[workers_index + 1]), 2)
        self.assertGreaterEqual(int(args[timeout_index + 1]), 90)


if __name__ == "__main__":
    unittest.main()

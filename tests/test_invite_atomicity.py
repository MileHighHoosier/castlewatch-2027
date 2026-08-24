import inspect
import unittest
from pathlib import Path

import invite_acceptance


class InviteAtomicityTests(unittest.TestCase):
    def test_invite_acceptance_locks_matching_row_before_consumption(self):
        source = inspect.getsource(invite_acceptance.accept_family_invite_atomic)

        self.assertIn("FOR UPDATE", source)
        self.assertIn("WHERE invite_prefix = :invite_prefix", source)
        # The row must be lockable even after another transaction changes status;
        # status is checked after the lock rather than filtered out of the SELECT.
        select_section = source.split("FOR UPDATE", 1)[0]
        self.assertNotIn("AND status = 'open'", select_section)
        self.assertIn('if invite["status"] != "open"', source)

    def test_invite_consumption_update_is_defensive_and_returns_confirmation(self):
        source = inspect.getsource(invite_acceptance.accept_family_invite_atomic)

        self.assertIn("SET status = 'accepted'", source)
        self.assertIn("AND status = 'open'", source)
        self.assertIn("RETURNING id::text AS id", source)
        self.assertIn("if consumed is None", source)

    def test_production_route_uses_atomic_invite_handler(self):
        source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("from invite_acceptance import accept_family_invite_atomic", source)
        self.assertIn("return accept_family_invite_atomic(engine)", source)

    def test_one_time_device_credential_response_is_not_cacheable(self):
        source = inspect.getsource(invite_acceptance.accept_family_invite_atomic)

        self.assertIn(
            'response.headers["Cache-Control"] = "no-store, max-age=0"',
            source,
        )


if __name__ == "__main__":
    unittest.main()

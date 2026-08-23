import inspect

import app
import invite_acceptance


def test_invite_acceptance_locks_matching_row_before_consumption():
    source = inspect.getsource(invite_acceptance.accept_family_invite_atomic)

    assert "FOR UPDATE" in source
    assert "WHERE invite_prefix = :invite_prefix" in source
    # The row must be lockable even after another transaction changes status;
    # status is checked after the lock rather than filtered out of the SELECT.
    select_section = source.split("FOR UPDATE", 1)[0]
    assert "AND status = 'open'" not in select_section
    assert 'if invite["status"] != "open"' in source


def test_invite_consumption_update_is_defensive_and_returns_confirmation():
    source = inspect.getsource(invite_acceptance.accept_family_invite_atomic)

    assert "SET status = 'accepted'" in source
    assert "AND status = 'open'" in source
    assert "RETURNING id::text AS id" in source
    assert "if consumed is None" in source


def test_production_route_uses_atomic_invite_handler():
    source = inspect.getsource(app.api_accept_family_invite)

    assert "accept_family_invite_atomic(engine)" in source

"""Unit tests that do not need a live database.

The app boots with an empty pool (min_size=0), so /health and the action->status
mapping are testable offline. Integration tests against a real PostgreSQL can be
added later behind a marker.
"""

from fastapi.testclient import TestClient

from app.logic import status_for_action
from app.main import app


def test_status_mapping():
    assert status_for_action("validate") == "validated"
    assert status_for_action("false_positive") == "false_positive"
    assert status_for_action("escalate") == "escalated"


def test_unknown_action_raises():
    try:
        status_for_action("nope")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

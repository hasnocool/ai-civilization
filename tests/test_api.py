# filename: test_api.py
"""API contract smoke tests."""

import pytest

try:
    from fastapi.testclient import TestClient
    from ai_civilization.api import app, manager
except ImportError:  # pragma: no cover
    TestClient = None


@pytest.mark.skipif(TestClient is None, reason="FastAPI test dependencies not installed")
def test_create_and_advance_game() -> None:
    manager.games.clear()
    client = TestClient(app)
    created = client.post("/games", json={"name": "Aurora", "seed": 7})
    assert created.status_code == 201
    game_id = created.json()["game_id"]

    advanced = client.post(f"/games/{game_id}/advance", json={"turns": 2})
    assert advanced.status_code == 200
    assert advanced.json()["state"]["turn"] == 3

    fetched = client.get(f"/games/{game_id}")
    assert fetched.status_code == 200
    assert fetched.json()["nation"]["name"] == "Aurora"

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_ok():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_chatgpt_healthz_ok():
    client = TestClient(app)
    response = client.get("/chatgpt-healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_chatgpt_write_healthz_ok():
    client = TestClient(app)
    response = client.get("/chatgpt-write-healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_claude_healthz_ok():
    client = TestClient(app)
    response = client.get("/claude-healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_claude_write_healthz_ok():
    client = TestClient(app)
    response = client.get("/claude-write-healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True

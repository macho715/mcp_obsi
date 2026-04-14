import importlib.util

from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app


def test_mcp_requires_bearer_when_token_present():
    client = TestClient(create_app())
    response = client.get("/mcp")
    assert response.status_code == 401


def test_mcp_allows_with_bearer_but_can_be_unavailable_without_dependency():
    with TestClient(create_app()) as client:
        response = client.get("/mcp", headers={"authorization": f"Bearer {settings.mcp_api_token}"})
    assert response.status_code in {200, 307, 405, 406, 421, 503}


def test_mcp_slash_path_is_not_not_found_when_dependency_is_installed():
    with TestClient(create_app()) as client:
        response = client.get(
            "/mcp/",
            headers={"authorization": f"Bearer {settings.mcp_api_token}"},
        )

    if importlib.util.find_spec("mcp") is None:
        assert response.status_code == 503
    else:
        assert response.status_code != 404


def test_chatgpt_mcp_does_not_require_bearer():
    with TestClient(create_app()) as client:
        response = client.get("/chatgpt-mcp")
    assert response.status_code in {200, 307, 405, 406, 421, 503}


def test_claude_mcp_does_not_require_bearer():
    with TestClient(create_app()) as client:
        response = client.get("/claude-mcp")
    assert response.status_code in {200, 307, 405, 406, 421, 503}


def test_chatgpt_mcp_write_requires_bearer():
    with TestClient(create_app()) as client:
        response = client.get("/chatgpt-mcp-write")
    assert response.status_code == 401


def test_chatgpt_mcp_write_allows_with_bearer_but_can_be_unavailable_without_dependency():
    with TestClient(create_app()) as client:
        response = client.get(
            "/chatgpt-mcp-write",
            headers={"authorization": f"Bearer {settings.effective_chatgpt_mcp_write_token}"},
        )
    assert response.status_code in {200, 307, 405, 406, 421, 503}


def test_claude_mcp_write_requires_bearer():
    with TestClient(create_app()) as client:
        response = client.get("/claude-mcp-write")
    assert response.status_code == 401


def test_claude_mcp_write_allows_with_bearer_but_can_be_unavailable_without_dependency():
    with TestClient(create_app()) as client:
        response = client.get(
            "/claude-mcp-write",
            headers={"authorization": f"Bearer {settings.effective_claude_mcp_write_token}"},
        )
    assert response.status_code in {200, 307, 405, 406, 421, 503}

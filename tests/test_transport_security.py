from pathlib import Path

from app.config import settings
from app.mcp_server import FastMCP, create_mcp_server
from app.services.memory_store import MemoryStore


def test_create_mcp_server_uses_configured_allowed_hosts_and_origins(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    original_hosts = settings.mcp_allowed_hosts
    original_origins = settings.mcp_allowed_origins
    settings.mcp_allowed_hosts = "preview.example.com"
    settings.mcp_allowed_origins = "https://preview.example.com"

    try:
        store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        server = create_mcp_server(store)
        assert server is not None
        assert server.settings.transport_security is not None
        assert server.settings.transport_security.allowed_hosts == ["preview.example.com"]
        assert server.settings.transport_security.allowed_origins == ["https://preview.example.com"]
    finally:
        settings.mcp_allowed_hosts = original_hosts
        settings.mcp_allowed_origins = original_origins


def test_create_mcp_server_augments_allowed_hosts_from_railway_runtime(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    original_public = settings.railway_public_domain
    original_static = settings.railway_static_url
    original_service = settings.railway_service_mcp_server_url
    settings.railway_public_domain = "prod.up.railway.app"
    settings.railway_static_url = "static.up.railway.app"
    settings.railway_service_mcp_server_url = "mcp.up.railway.app"

    try:
        store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
        server = create_mcp_server(store)
        assert server is not None
        assert server.settings.transport_security is not None
        assert server.settings.transport_security.allowed_hosts == [
            "prod.up.railway.app",
            "static.up.railway.app",
            "mcp.up.railway.app",
        ]
        assert server.settings.transport_security.allowed_origins == [
            "https://prod.up.railway.app",
            "https://static.up.railway.app",
            "https://mcp.up.railway.app",
        ]
    finally:
        settings.railway_public_domain = original_public
        settings.railway_static_url = original_static
        settings.railway_service_mcp_server_url = original_service

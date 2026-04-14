from __future__ import annotations

import contextlib

from fastapi import FastAPI

from app.auth import BearerTokenMiddleware
from app.config import settings
from app.mcp_server import create_mcp_server
from app.services.index_store import IndexStore
from app.services.memory_store import MemoryStore

index_store = IndexStore(settings.index_db_path)
memory_store = MemoryStore(settings.vault_path, index_store=index_store, timezone=settings.timezone)
mcp = create_mcp_server(memory_store)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    BearerTokenMiddleware,
    token=settings.mcp_api_token,
    exempt_paths={"/healthz"},
)


@app.get("/healthz")
async def healthz() -> dict:
    return {
        "ok": True,
        "app": settings.app_name,
        "vault_path": str(settings.vault_path),
        "db_path": str(settings.index_db_path),
    }


app.mount("/mcp", app=mcp.streamable_http_app())

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.chatgpt_mcp_server import create_chatgpt_mcp_server
from app.config import settings
from app.services.memory_store import MemoryStore


def create_chatgpt_app() -> FastAPI:
    store = MemoryStore(settings.vault_path, settings.index_db_path, timezone=settings.timezone)
    mcp = create_chatgpt_mcp_server(store)
    mcp_write = create_chatgpt_mcp_server(store, include_write_tools=True)
    mcp_app = mcp.streamable_http_app() if mcp is not None else None
    mcp_write_app = mcp_write.streamable_http_app() if mcp_write is not None else None

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if mcp is None and mcp_write is None:
            yield
            return

        if mcp is not None and mcp_write is not None:
            async with mcp.session_manager.run(), mcp_write.session_manager.run():
                yield
            return

        target = mcp or mcp_write
        assert target is not None
        async with target.session_manager.run():
            yield

    app = FastAPI(title=f"{settings.app_name}-chatgpt", lifespan=lifespan)

    @app.get("/")
    async def root() -> dict:
        return {"ok": True, "profile": "chatgpt-tool-only"}

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True, "service": f"{settings.app_name}-chatgpt"}

    @app.get("/write-healthz")
    async def write_healthz() -> dict:
        return {"ok": True, "service": f"{settings.app_name}-chatgpt-write"}

    @app.middleware("http")
    async def bearer_auth(request: Request, call_next):
        expected = ""
        if request.url.path.startswith("/mcp-write"):
            expected = settings.effective_chatgpt_mcp_write_token
        elif request.url.path.startswith("/mcp"):
            expected = settings.mcp_api_token
        if expected:
            auth = request.headers.get("authorization", "")
            if auth != f"Bearer {expected}":
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)

    if mcp_app is not None:
        app.mount("/mcp", mcp_app)
    else:

        @app.api_route("/mcp/{path:path}", methods=["GET", "POST"])
        async def mcp_not_ready(path: str = "") -> JSONResponse:
            _ = path
            return JSONResponse(
                {
                    "error": "mcp_dependency_missing",
                    "message": "Install optional dependencies with: pip install -e .[mcp]",
                },
                status_code=503,
            )

    if mcp_write_app is not None:
        app.mount("/mcp-write", mcp_write_app)
    else:

        @app.api_route("/mcp-write/{path:path}", methods=["GET", "POST"])
        async def mcp_write_not_ready(path: str = "") -> JSONResponse:
            _ = path
            return JSONResponse(
                {
                    "error": "mcp_dependency_missing",
                    "message": "Install optional dependencies with: pip install -e .[mcp]",
                },
                status_code=503,
            )

    return app


app = create_chatgpt_app()

from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.chatgpt_mcp_server import create_chatgpt_mcp_server
from app.claude_mcp_server import create_claude_mcp_server
from app.config import settings
from app.mcp_server import create_mcp_server
from app.services.memory_store import MemoryStore


def create_app() -> FastAPI:
    store = MemoryStore(settings.vault_path, settings.index_db_path, timezone=settings.timezone)
    mcp = create_mcp_server(store)
    chatgpt_mcp = create_chatgpt_mcp_server(store)
    chatgpt_mcp_write = create_chatgpt_mcp_server(store, include_write_tools=True)
    claude_mcp = create_claude_mcp_server(store)
    claude_mcp_write = create_claude_mcp_server(store, include_write_tools=True)
    mcp_app = mcp.streamable_http_app() if mcp is not None else None
    chatgpt_mcp_app = chatgpt_mcp.streamable_http_app() if chatgpt_mcp is not None else None
    chatgpt_mcp_write_app = (
        chatgpt_mcp_write.streamable_http_app() if chatgpt_mcp_write is not None else None
    )
    claude_mcp_app = claude_mcp.streamable_http_app() if claude_mcp is not None else None
    claude_mcp_write_app = (
        claude_mcp_write.streamable_http_app() if claude_mcp_write is not None else None
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with AsyncExitStack() as stack:
            if mcp is not None:
                await stack.enter_async_context(mcp.session_manager.run())
            if chatgpt_mcp is not None:
                await stack.enter_async_context(chatgpt_mcp.session_manager.run())
            if chatgpt_mcp_write is not None:
                await stack.enter_async_context(chatgpt_mcp_write.session_manager.run())
            if claude_mcp is not None:
                await stack.enter_async_context(claude_mcp.session_manager.run())
            if claude_mcp_write is not None:
                await stack.enter_async_context(claude_mcp_write.session_manager.run())
            yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True, "service": settings.app_name}

    @app.get("/chatgpt-healthz")
    async def chatgpt_healthz() -> dict:
        return {"ok": True, "service": f"{settings.app_name}-chatgpt"}

    @app.get("/chatgpt-write-healthz")
    async def chatgpt_write_healthz() -> dict:
        return {"ok": True, "service": f"{settings.app_name}-chatgpt-write"}

    @app.get("/claude-healthz")
    async def claude_healthz() -> dict:
        return {"ok": True, "service": f"{settings.app_name}-claude"}

    @app.get("/claude-write-healthz")
    async def claude_write_healthz() -> dict:
        return {"ok": True, "service": f"{settings.app_name}-claude-write"}

    def _expected_bearer_for_path(path: str) -> str:
        if path.startswith("/chatgpt-mcp-write"):
            return settings.effective_chatgpt_mcp_write_token
        if path.startswith("/claude-mcp-write"):
            return settings.effective_claude_mcp_write_token
        if path.startswith("/mcp"):
            return settings.mcp_api_token
        return ""

    @app.middleware("http")
    async def bearer_auth(request: Request, call_next):
        expected = _expected_bearer_for_path(request.url.path)
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

    if chatgpt_mcp_app is not None:
        app.mount("/chatgpt-mcp", chatgpt_mcp_app)
    else:

        @app.api_route("/chatgpt-mcp/{path:path}", methods=["GET", "POST"])
        async def chatgpt_mcp_not_ready(path: str = "") -> JSONResponse:
            _ = path
            return JSONResponse(
                {
                    "error": "mcp_dependency_missing",
                    "message": "Install optional dependencies with: pip install -e .[mcp]",
                },
                status_code=503,
            )

    if chatgpt_mcp_write_app is not None:
        app.mount("/chatgpt-mcp-write", chatgpt_mcp_write_app)
    else:

        @app.api_route("/chatgpt-mcp-write/{path:path}", methods=["GET", "POST"])
        async def chatgpt_mcp_write_not_ready(path: str = "") -> JSONResponse:
            _ = path
            return JSONResponse(
                {
                    "error": "mcp_dependency_missing",
                    "message": "Install optional dependencies with: pip install -e .[mcp]",
                },
                status_code=503,
            )

    if claude_mcp_app is not None:
        app.mount("/claude-mcp", claude_mcp_app)
    else:

        @app.api_route("/claude-mcp/{path:path}", methods=["GET", "POST"])
        async def claude_mcp_not_ready(path: str = "") -> JSONResponse:
            _ = path
            return JSONResponse(
                {
                    "error": "mcp_dependency_missing",
                    "message": "Install optional dependencies with: pip install -e .[mcp]",
                },
                status_code=503,
            )

    if claude_mcp_write_app is not None:
        app.mount("/claude-mcp-write", claude_mcp_write_app)
    else:

        @app.api_route("/claude-mcp-write/{path:path}", methods=["GET", "POST"])
        async def claude_mcp_write_not_ready(path: str = "") -> JSONResponse:
            _ = path
            return JSONResponse(
                {
                    "error": "mcp_dependency_missing",
                    "message": "Install optional dependencies with: pip install -e .[mcp]",
                },
                status_code=503,
            )

    return app


app = create_app()

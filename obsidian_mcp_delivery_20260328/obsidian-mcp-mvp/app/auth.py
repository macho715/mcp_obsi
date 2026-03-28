from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str | None = None, exempt_paths: set[str] | None = None):
        super().__init__(app)
        self.token = token
        self.exempt_paths = exempt_paths or {"/healthz"}

    async def dispatch(self, request: Request, call_next):
        if not self.token or request.url.path in self.exempt_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        expected = f"Bearer {self.token}"
        if auth_header != expected:
            return JSONResponse(
                status_code=401,
                content={"ok": False, "error": "Unauthorized"},
            )
        return await call_next(request)

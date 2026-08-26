from __future__ import annotations

from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send


class SpaStaticFiles(StaticFiles):
    """Serve the Vue build and fall back to index.html for client-side routes."""

    async def get_response(self, path: str, scope: Scope):  # type: ignore[no-untyped-def]
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            response = await super().get_response("index.html", scope)

        if response.status_code == 404:
            return await super().get_response("index.html", scope)
        return response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await super().__call__(scope, receive, send)


def frontend_build_path() -> Path:
    return Path(__file__).resolve().parent / "static"

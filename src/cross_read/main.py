from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cross_read import __version__
from cross_read.api.router import api_router
from cross_read.core.config import AppConfig, load_config
from cross_read.core.errors import register_error_handlers
from cross_read.core.paths import ShareRegistry
from cross_read.web import SpaStaticFiles, frontend_build_path


def create_app(config: AppConfig | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        active_config = config
        if active_config is None:
            config_path = os.environ.get("CROSS_READ_CONFIG", "config.yaml")
            active_config = load_config(config_path)

        app.state.config = active_config
        app.state.share_registry = ShareRegistry(active_config)
        yield

    application = FastAPI(
        title="Cross Read",
        description="局域网只读文件阅读服务",
        version=__version__,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "HEAD", "OPTIONS"],
        allow_headers=["Range", "Content-Type"],
    )
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")
    static_path = frontend_build_path()
    if (static_path / "index.html").is_file():
        application.mount("/", SpaStaticFiles(directory=static_path, html=True), name="frontend")
    return application


app = create_app()

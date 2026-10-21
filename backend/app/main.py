"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.http.security_headers import SecurityHeadersMiddleware
from app.http.spa import build_spa_router
from app.store.db import create_db_engine, init_db


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        engine = create_db_engine(settings.database_path)
        init_db(engine)
        app.state.engine = engine
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="OfficeHand",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.api_docs_enabled else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.api_docs_enabled else None,
    )
    app.state.settings = settings
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # The SPA catch-all must be registered last so API routes take precedence.
    app.include_router(build_spa_router(settings.frontend_dist))
    return app

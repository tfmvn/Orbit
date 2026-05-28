"""Application entrypoint: builds and configures the FastAPI app.

Run locally with:

    uvicorn orbit_api.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orbit_api import __version__
from orbit_api.api.v1.router import router as v1_router
from orbit_api.config import get_settings
from orbit_api.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown hooks.

    Future subsystems (runtime, tool provider, memory provider) will be
    constructed and torn down here once they exist, and attached to
    `app.state` for dependency providers to pick up.
    """
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger("orbit_api")
    logger.info("startup", environment=settings.environment)
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="Orbit API",
        description="Foundation-phase backend for the Orbit AI runtime.",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)

    return app


app = create_app()

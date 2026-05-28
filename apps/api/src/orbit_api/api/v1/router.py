"""Aggregates all v1 routers into a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from orbit_api.api.v1 import health, version

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(version.router)

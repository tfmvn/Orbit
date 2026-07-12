"""Aggregates all v1 routers into a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from orbit_api.api.v1 import context, git, health, process, search, tasks, tools, version, workspace

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(version.router)
router.include_router(tasks.router)
router.include_router(tools.router)
router.include_router(process.router)
router.include_router(workspace.router)
router.include_router(search.router)
router.include_router(context.router)
router.include_router(git.router)

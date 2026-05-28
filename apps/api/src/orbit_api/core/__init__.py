"""Application-wide wiring: dependency providers used across routes.

This is the one place route modules should reach into for shared
dependencies (settings, logger, and — once implemented — the runtime,
planner, tool provider, memory provider, and model provider). Keeping this
centralized avoids routes importing concrete implementations directly and
keeps `apps/api` free of circular imports.
"""

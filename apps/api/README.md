# orbit-api

FastAPI backend for Orbit. See the [root README](../../README.md) for full
project context.

## Run locally

```bash
pip install -e ".[dev]"
cp .env.example .env
uvicorn orbit_api.main:app --reload
```

## Test

```bash
pytest
```

## Layout

```
src/orbit_api/
├── main.py         # app factory / entrypoint
├── config.py       # Settings (pydantic-settings)
├── logging.py      # structlog configuration
├── core/           # DI providers used by routes
├── api/v1/         # versioned HTTP routes
└── interfaces/     # abstract contracts for future subsystems
```

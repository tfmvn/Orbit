"""Model Provider endpoints: list providers, health, available models, generate.

Exposes `orbit_providers.ProviderManager` over HTTP. Returns structured
JSON only — no chat endpoint, no conversation state; this is the
provider-integration surface a future planner will consume instead of
calling a provider directly.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from orbit_context import ContextEngineError
from orbit_providers import (
    GenerationParameters,
    GenerationRequest,
    ModelProvider,
    NoActiveProviderError,
    ProviderError,
    ProviderNotFoundError,
)
from pydantic import BaseModel

from orbit_api.core.dependencies import ContextEngineDep, ProviderManagerDep

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderSummaryResponse(BaseModel):
    name: str
    active: bool


class ModelInfoResponse(BaseModel):
    name: str
    size: int | None
    modified_at: str | None


class ProviderHealthResponse(BaseModel):
    healthy: bool
    provider: str
    detail: str | None
    checked_at: float


class ActivateProviderRequest(BaseModel):
    name: str


class GenerateRequest(BaseModel):
    prompt: str
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: list[str] | None = None
    context_query: str | None = None
    context_paths: list[str] | None = None


class GenerateResponse(BaseModel):
    text: str
    model: str
    provider: str
    duration: float


def _resolve_provider(manager: ProviderManagerDep, name: str | None) -> ModelProvider:
    """Look up `name`, or fall back to the active provider if `name` is `None`."""
    if name is None:
        try:
            return manager.active_provider
        except NoActiveProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    provider = manager.get(name)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"No provider registered with name '{name}'")
    return provider


@router.get("", response_model=list[ProviderSummaryResponse], summary="List registered providers")
async def list_providers(manager: ProviderManagerDep) -> list[ProviderSummaryResponse]:
    return [ProviderSummaryResponse(name=name, active=name == manager.active) for name in manager.list()]


@router.get("/health", response_model=ProviderHealthResponse, summary="Check provider health")
async def provider_health(
    manager: ProviderManagerDep, provider: str | None = None
) -> ProviderHealthResponse:
    target = _resolve_provider(manager, provider)
    health = await target.health()
    return ProviderHealthResponse(**health.to_dict())


@router.get("/models", response_model=list[ModelInfoResponse], summary="List available models")
async def list_models(manager: ProviderManagerDep, provider: str | None = None) -> list[ModelInfoResponse]:
    target = _resolve_provider(manager, provider)
    try:
        models = await target.list_models()
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [ModelInfoResponse(**m.to_dict()) for m in models]


@router.post("/active", response_model=ProviderSummaryResponse, summary="Switch the active provider")
async def set_active_provider(
    body: ActivateProviderRequest, manager: ProviderManagerDep
) -> ProviderSummaryResponse:
    try:
        manager.set_active(body.name)
    except ProviderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProviderSummaryResponse(name=body.name, active=True)


@router.post("/generate", response_model=GenerateResponse, summary="Generate a completion")
async def generate(
    body: GenerateRequest, manager: ProviderManagerDep, context_engine: ContextEngineDep
) -> GenerateResponse:
    target = _resolve_provider(manager, body.provider)

    context = None
    if body.context_query or body.context_paths:
        try:
            context = await context_engine.build_context(query=body.context_query, paths=body.context_paths)
        except ContextEngineError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    request = GenerationRequest(
        prompt=body.prompt,
        model=body.model,
        context=context,
        parameters=GenerationParameters(
            temperature=body.temperature,
            top_p=body.top_p,
            max_tokens=body.max_tokens,
            stop=body.stop,
        ),
    )
    try:
        result = await target.generate(request)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GenerateResponse(text=result.text, model=result.model, provider=result.provider, duration=result.duration)

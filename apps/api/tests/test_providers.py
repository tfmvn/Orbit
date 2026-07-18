from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def test_list_providers_includes_ollama() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/providers")
        assert response.status_code == 200
        names = [p["name"] for p in response.json()]
        assert "ollama" in names


async def test_provider_health_never_raises() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/providers/health")
        assert response.status_code == 200
        body = response.json()
        assert "healthy" in body
        assert body["provider"] == "ollama"


async def test_provider_health_unknown_provider_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/providers/health", params={"provider": "missing"})
        assert response.status_code == 404


async def test_set_active_unknown_provider_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/providers/active", json={"name": "missing"})
        assert response.status_code == 404


async def test_generate_reports_structured_error_when_unreachable() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/providers/generate", json={"prompt": "hello"})
        # No live Ollama server in the test environment: the provider must
        # surface this as a structured 502, never an unhandled exception.
        assert response.status_code == 502
        assert "detail" in response.json()

from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def test_project_summary_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/context/summary")
        assert response.status_code == 200
        body = response.json()
        assert "workspace" in body
        assert "stats" in body


async def test_workspace_stats_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/context/stats")
        assert response.status_code == 200
        assert "total_files" in response.json()


async def test_generate_context_requires_query_or_paths() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/context/generate", json={})
        assert response.status_code == 400


async def test_generate_context_from_query() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/context/generate", json={"query": "import"})
        assert response.status_code == 200
        body = response.json()
        assert "files" in body
        assert "matches" in body
        assert "truncated" in body

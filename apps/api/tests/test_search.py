from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def test_search_tool_is_registered() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/search")
        assert response.status_code == 200
        assert response.json()["name"] == "search"


async def test_index_status_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/index")
        assert response.status_code == 200
        body = response.json()
        assert "file_count" in body
        assert "root" in body


async def test_refresh_index_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/search/index/refresh")
        assert response.status_code == 200
        assert "file_count" in response.json()


async def test_search_endpoint_rejects_empty_query() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/search", json={"query": ""})
        assert response.status_code == 400

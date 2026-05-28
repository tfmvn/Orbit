from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def test_version_returns_expected_fields() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/version")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "orbit-api"
    assert "version" in body
    assert "environment" in body

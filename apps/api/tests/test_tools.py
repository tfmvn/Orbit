from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def test_list_tools_includes_builtins() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tools")
        assert response.status_code == 200
        names = {tool["name"] for tool in response.json()}
        assert {"echo", "time", "system_info"} <= names


async def test_get_tool_metadata() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/echo")
        assert response.status_code == 200
        assert response.json()["name"] == "echo"


async def test_get_unknown_tool_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/does-not-exist")
        assert response.status_code == 404


async def test_execute_echo_tool() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tools/echo/execute", json={"arguments": {"message": "hi"}}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["output"] == {"echo": "hi"}


async def test_execute_echo_tool_missing_argument_returns_failure_result() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/tools/echo/execute", json={"arguments": {}})
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert body["error"] is not None


async def test_execute_unknown_tool_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/tools/does-not-exist/execute", json={})
        assert response.status_code == 404

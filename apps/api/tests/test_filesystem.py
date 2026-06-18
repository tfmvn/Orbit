from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def test_workspace_info() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/workspace")
        assert response.status_code == 200
        body = response.json()
        assert "root" in body
        assert body["exists"] is True


async def test_filesystem_tool_is_registered() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tools/filesystem")
        assert response.status_code == 200
        assert response.json()["name"] == "filesystem"


async def test_filesystem_create_and_read_via_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/api/v1/tools/filesystem/execute",
            json={"arguments": {"operation": "create", "path": "api-test.txt", "content": "hi"}},
        )
        assert create.status_code == 200
        assert create.json()["success"] is True

        read = await client.post(
            "/api/v1/tools/filesystem/execute",
            json={"arguments": {"operation": "read", "path": "api-test.txt"}},
        )
        assert read.status_code == 200
        assert read.json()["output"]["content"] == "hi"

        cleanup = await client.post(
            "/api/v1/tools/filesystem/execute",
            json={"arguments": {"operation": "delete", "path": "api-test.txt"}},
        )
        assert cleanup.json()["success"] is True


async def test_filesystem_path_traversal_rejected_via_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tools/filesystem/execute",
            json={"arguments": {"operation": "read", "path": "../outside.txt"}},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert "workspace" in body["error"]

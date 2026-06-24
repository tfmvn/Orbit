import asyncio

from httpx import ASGITransport, AsyncClient

from orbit_api.main import app


async def _await_completion(client, execution_id, timeout=2.0):
    async def _poll():
        while True:
            response = await client.get(f"/api/v1/process/{execution_id}/status")
            if response.json()["status"] != "running":
                return
            await asyncio.sleep(0.01)

    await asyncio.wait_for(_poll(), timeout=timeout)


async def test_execute_then_poll_result() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/process/execute", json={"command": ["echo", "hi"]})
        assert response.status_code == 200
        execution_id = response.json()["id"]

        await _await_completion(client, execution_id)

        result = await client.get(f"/api/v1/process/{execution_id}/result")
        assert result.status_code == 200
        body = result.json()
        assert body["status"] == "completed"
        assert body["exit_code"] == 0
        assert body["stdout"].strip() == "hi"


async def test_unknown_execution_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/process/does-not-exist/status")
        assert response.status_code == 404


async def test_execute_rejects_command_outside_workspace() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/process/execute", json={"command": ["echo", "hi"], "cwd": "../outside"}
        )
        assert response.status_code == 400

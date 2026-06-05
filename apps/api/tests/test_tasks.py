import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from orbit_api.core.runtime import get_runtime
from orbit_api.main import app


@pytest.fixture(autouse=True)
async def _running_runtime():
    """Start/stop the runtime's worker pool around each test.

    `ASGITransport` doesn't trigger the app's lifespan, so the singleton
    runtime (shared with the app via `get_runtime()`) is started here
    instead -- otherwise submitted tasks would never leave the queue.
    """
    runtime = get_runtime()
    await runtime.start()
    yield
    await runtime.stop()
    get_runtime.cache_clear()


async def _wait_until_terminal(task_id: str, client: AsyncClient, attempts: int = 50) -> dict:
    body: dict = {}
    for _ in range(attempts):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        body = response.json()
        if body["status"] in ("completed", "failed", "cancelled"):
            return body
        await asyncio.sleep(0.01)
    return body


async def test_submit_task_without_handler_fails_gracefully() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        submit = await client.post("/api/v1/tasks", json={"name": "unregistered", "payload": {}})
        assert submit.status_code == 201
        task_id = submit.json()["id"]
        assert submit.json()["status"] == "queued"

        body = await _wait_until_terminal(task_id, client)
        assert body["status"] == "failed"
        assert "unregistered" in body["error"]


async def test_list_and_cancel_task() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        submit = await client.post("/api/v1/tasks", json={"name": "slow", "payload": {}})
        task_id = submit.json()["id"]

        listed = await client.get("/api/v1/tasks")
        assert listed.status_code == 200
        assert any(t["id"] == task_id for t in listed.json())

        cancel = await client.post(f"/api/v1/tasks/{task_id}/cancel")
        assert cancel.status_code == 200
        # Cancellation is immediate unless the worker already picked it up.
        assert cancel.json()["status"] in ("cancelled", "running", "failed")


async def test_get_unknown_task_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks/does-not-exist")
        assert response.status_code == 404


async def test_cancel_unknown_task_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/tasks/does-not-exist/cancel")
        assert response.status_code == 404

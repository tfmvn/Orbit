import asyncio

import pytest

from orbit_runtime import EventType, Runtime, TaskStatus


@pytest.fixture
async def runtime():
    rt = Runtime(num_workers=1)
    await rt.start()
    yield rt
    await rt.stop()


async def test_submit_runs_handler_and_completes(runtime):
    async def echo(task):
        return task.payload["value"]

    runtime.register_handler("echo", echo)
    task = await runtime.submit("echo", {"value": 42})

    for _ in range(50):
        if runtime.get(task.id).status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            break
        await asyncio.sleep(0.01)

    finished = runtime.get(task.id)
    assert finished.status == TaskStatus.COMPLETED
    assert finished.result == 42


async def test_missing_handler_fails_task(runtime):
    task = await runtime.submit("unregistered-type", {})

    for _ in range(50):
        if runtime.get(task.id).status == TaskStatus.FAILED:
            break
        await asyncio.sleep(0.01)

    finished = runtime.get(task.id)
    assert finished.status == TaskStatus.FAILED
    assert "unregistered-type" in finished.error


async def test_cancel_queued_task_is_immediate():
    rt = Runtime(num_workers=0)  # no worker running, task stays queued
    task = await rt.submit("noop", {})
    cancelled = await rt.cancel(task.id)
    assert cancelled.status == TaskStatus.CANCELLED


async def test_events_are_emitted_in_order(runtime):
    seen: list[EventType] = []
    runtime.events.subscribe_all(lambda e: seen.append(e.type))

    async def noop(task):
        return None

    runtime.register_handler("noop", noop)
    task = await runtime.submit("noop", {})

    for _ in range(50):
        if runtime.get(task.id).status == TaskStatus.COMPLETED:
            break
        await asyncio.sleep(0.01)

    assert seen == [
        EventType.TASK_CREATED,
        EventType.TASK_QUEUED,
        EventType.TASK_STARTED,
        EventType.TASK_COMPLETED,
    ]


async def test_list_filters_by_status():
    rt = Runtime(num_workers=0)
    await rt.submit("a", {})
    await rt.submit("b", {})
    assert len(rt.list()) == 2
    assert len(rt.list(status=TaskStatus.QUEUED)) == 2
    assert len(rt.list(status=TaskStatus.COMPLETED)) == 0

import pytest

from orbit_runtime.task import InvalidTransitionError, Task, TaskStatus


def test_new_task_starts_created():
    task = Task(name="demo")
    assert task.status == TaskStatus.CREATED
    assert not task.is_terminal


def test_valid_transition_sequence():
    task = Task(name="demo")
    task.transition_to(TaskStatus.QUEUED)
    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED
    assert task.is_terminal


@pytest.mark.parametrize(
    "start,target",
    [
        (TaskStatus.CREATED, TaskStatus.RUNNING),
        (TaskStatus.CREATED, TaskStatus.COMPLETED),
        (TaskStatus.QUEUED, TaskStatus.COMPLETED),
        (TaskStatus.COMPLETED, TaskStatus.RUNNING),
        (TaskStatus.FAILED, TaskStatus.QUEUED),
        (TaskStatus.CANCELLED, TaskStatus.RUNNING),
    ],
)
def test_invalid_transitions_are_rejected(start, target):
    task = Task(name="demo", status=start)
    with pytest.raises(InvalidTransitionError):
        task.transition_to(target)

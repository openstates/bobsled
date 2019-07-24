import time
import pytest
from ..base import Task, Run, Status
from ..runners import LocalRunService, MemoryRunPersister


@pytest.mark.asyncio
async def test_simple_run():
    lrs = LocalRunService(MemoryRunPersister())
    task = Task("hello-world", image="hello-world")
    run = await lrs.run_task(task)

    assert run.status == Status.Running

    # wait a maximum of 2 seconds
    ticks = 0
    while ticks < 20:
        lrs.update_status(run)
        n_running = len(await lrs.get_runs(status=Status.Running))
        if n_running == 0:
            break
        time.sleep(0.1)
        ticks += 1

    assert n_running == 0
    assert len(await lrs.get_runs(status=Status.Success)) == 1
    await lrs.cleanup()


@pytest.mark.asyncio
async def test_get_logs():
    lrs = LocalRunService(MemoryRunPersister())
    task = Task("hello-world", image="hello-world")
    run = await lrs.run_task(task)
    assert "Hello from Docker" in lrs.get_logs(run)
    await lrs.cleanup()

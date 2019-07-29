import time
import pytest
from ..base import Task, Run, Status
from ..runners import LocalRunService, MemoryRunPersister
from ..exceptions import AlreadyRunning


def local_run_service():
    return LocalRunService(MemoryRunPersister())



@pytest.mark.parametrize("Cls", [local_run_service])
@pytest.mark.asyncio
async def test_simple_run(Cls):
    rs = Cls()
    task = Task("hello-world", image="hello-world")
    run = await rs.run_task(task)

    assert run.status == Status.Running

    # wait a maximum of 2 seconds
    ticks = 0
    while ticks < 20:
        await rs.update_status(run.uuid)
        n_running = len(await rs.get_runs(status=Status.Running))
        if n_running == 0:
            break
        time.sleep(0.1)
        ticks += 1

    assert n_running == 0
    runs = await rs.get_runs(status=Status.Success)
    assert len(runs) == 1
    assert "Hello from Docker" in runs[0].logs
    assert await rs.cleanup() == 0


@pytest.mark.parametrize("Cls", [local_run_service])
@pytest.mark.asyncio
async def test_stop_run(Cls):
    rs = Cls()
    # run forever task, then kill it
    task = Task("forever", image="forever")
    run = await rs.run_task(task)
    run = await rs.update_status(run.uuid, update_logs=True)
    assert "still alive..." in run.logs
    await rs.stop_run(run.uuid)

    run = await rs.get_run(run.uuid)
    assert run.status == Status.UserKilled
    assert await rs.cleanup() == 0


@pytest.mark.parametrize("Cls", [local_run_service])
@pytest.mark.asyncio
async def test_cleanup(Cls):
    rs = Cls()
    # run forever task
    task = Task("forever", image="forever")
    run = await rs.run_task(task)

    assert await rs.cleanup() == 1


@pytest.mark.parametrize("Cls", [local_run_service])
@pytest.mark.asyncio
async def test_already_running(Cls):
    rs = Cls()
    task = Task("forever", image="forever")
    await rs.run_task(task)
    with pytest.raises(AlreadyRunning):
        await rs.run_task(task)

    assert await rs.cleanup() == 1


@pytest.mark.parametrize("Cls", [local_run_service])
@pytest.mark.asyncio
async def test_timeout(Cls):
    rs = Cls()
    task = Task("timeout", image="forever", timeout_minutes=(1/60.))
    run = await rs.run_task(task)

    assert run.status == Status.Running

    # wait a maximum of 2 seconds
    ticks = 0
    while ticks < 20:
        await rs.update_status(run.uuid)
        n_running = len(await rs.get_runs(status=Status.Running))
        if n_running == 0:
            break
        time.sleep(0.1)
        ticks += 1

    assert n_running == 0
    assert len(await rs.get_runs(status=Status.TimedOut)) == 1
    assert await rs.cleanup() == 0

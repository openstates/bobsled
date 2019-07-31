import os
import time
import pytest
from ..base import Task, Status
from ..runners import LocalRunService, ECSRunService, MemoryRunPersister
from ..exceptions import AlreadyRunning


def local_run_service():
    return LocalRunService(MemoryRunPersister())


def ecs_run_service():
    cluster_name = os.environ.get("TEST_CLUSTER")
    subnet_id = os.environ.get("TEST_SUBNET")
    security_group_id = os.environ.get("TEST_SECURITY_GROUP")
    if cluster_name and subnet_id and security_group_id:
        return ECSRunService(
            MemoryRunPersister(),
            cluster_name=cluster_name,
            subnet_id=subnet_id,
            security_group_id=security_group_id,
            log_group="bobsled",
        )


@pytest.mark.parametrize("Cls", [local_run_service, ecs_run_service])
@pytest.mark.asyncio
async def test_simple_run(Cls):
    rs = Cls()
    if not rs:
        pytest.skip("ECS not configured")
    task = Task("hello-world", image="hello-world")
    run = await rs.run_task(task)

    assert run.status == Status.Running

    # wait for a while
    ticks = 0
    while ticks < 60000:
        await rs.update_status(run.uuid)
        n_running = len(await rs.get_runs(status=[Status.Running, Status.Pending]))
        if n_running == 0:
            break
        time.sleep(0.1)
        ticks += 1

    assert n_running == 0
    runs = await rs.get_runs(status=Status.Success)
    assert len(runs) == 1
    assert "Hello from Docker" in runs[0].logs
    assert await rs.cleanup() == 0


@pytest.mark.parametrize("Cls", [local_run_service, ecs_run_service])
@pytest.mark.asyncio
async def test_stop_run(Cls):
    rs = Cls()
    if not rs:
        pytest.skip("ECS not configured")
    # run forever task, then kill it
    task = Task("forever", image="forever")
    run = await rs.run_task(task)
    run = await rs.update_status(run.uuid, update_logs=True)
    await rs.stop_run(run.uuid)

    run = await rs.update_status(run.uuid, update_logs=True)
    assert run.status == Status.UserKilled
    assert await rs.cleanup() == 0


@pytest.mark.parametrize("Cls", [local_run_service, ecs_run_service])
@pytest.mark.asyncio
async def test_cleanup(Cls):
    rs = Cls()
    if not rs:
        pytest.skip("ECS not configured")
    # run forever task
    task = Task("forever", image="forever")
    await rs.run_task(task)

    assert await rs.cleanup() == 1


# doesn't need to be tested on multiple services since logic is in base class
@pytest.mark.parametrize("Cls", [local_run_service])
@pytest.mark.asyncio
async def test_already_running(Cls):
    rs = Cls()
    if not rs:
        pytest.skip("ECS not configured")
    task = Task("forever", image="forever")
    await rs.run_task(task)
    with pytest.raises(AlreadyRunning):
        await rs.run_task(task)

    assert await rs.cleanup() == 1


@pytest.mark.parametrize("Cls", [local_run_service, ecs_run_service])
@pytest.mark.asyncio
async def test_timeout(Cls):
    rs = Cls()
    if not rs:
        pytest.skip("ECS not configured")
    task = Task("timeout", image="forever", timeout_minutes=(1 / 60.0))
    run = await rs.run_task(task)

    assert run.status == Status.Running

    # wait a maximum of 2 seconds
    ticks = 0
    while ticks < 20:
        await rs.update_status(run.uuid)
        n_running = len(await rs.get_runs(status=[Status.Running, Status.Pending]))
        if n_running == 0:
            break
        time.sleep(0.1)
        ticks += 1

    assert n_running == 0
    assert len(await rs.get_runs(status=Status.TimedOut)) == 1
    assert await rs.cleanup() == 0

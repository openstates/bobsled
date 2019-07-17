import time
from ..base import Task, Run, Status
from ..local_run_service import LocalRunService


def test_simple_run():
    lrs = LocalRunService()
    task = Task("hello-world", image="hello-world")
    run = lrs.run_task(task)

    assert run.status == Status.Running

    # wait a maximum of 2 seconds
    ticks = 0
    while ticks < 20:
        lrs.update_statuses()
        n_running = len(lrs.get_runs(status=Status.Running))
        if n_running == 0:
            break
        time.sleep(0.1)
        ticks += 1

    assert n_running == 0
    assert len(lrs.get_runs(status=Status.Success)) == 1
    lrs.cleanup()


def test_get_logs():
    lrs = LocalRunService()
    task = Task("hello-world", image="hello-world")
    run = lrs.run_task(task)
    assert b"Hello from Docker" in lrs.get_logs(run)
    lrs.cleanup()

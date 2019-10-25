import os
import pytest
from ..runners import MemoryRunPersister, DatabaseRunPersister
from ..base import Run, Status


def db_persister():
    try:
        os.remove("test.db")
    except OSError:
        pass
    db = DatabaseRunPersister("sqlite:///test.db")
    return db


@pytest.mark.parametrize("cls", [MemoryRunPersister, db_persister])
@pytest.mark.asyncio
async def test_simple_add_then_get(cls):
    p = cls()
    await p.connect()
    r = Run("test-task", Status.Running)
    await p.add_run(r)
    r2 = await p.get_run(r.uuid)
    assert r.task == r2.task
    assert r.uuid == r2.uuid
    assert r.status == r2.status


@pytest.mark.parametrize("cls", [MemoryRunPersister, db_persister])
@pytest.mark.asyncio
async def test_update(cls):
    p = cls()
    await p.connect()
    r = Run("test-task", Status.Running)
    await p.add_run(r)
    r.status = Status.Success
    r.exit_code = 0
    await p.save_run(r)
    r2 = await p.get_run(r.uuid)
    assert r2.status == Status.Success
    assert r2.exit_code == 0


@pytest.mark.parametrize("cls", [MemoryRunPersister, db_persister])
@pytest.mark.asyncio
async def test_bad_get(cls):
    p = cls()
    await p.connect()
    r = await p.get_run("nonsense")
    assert r is None


@pytest.mark.parametrize("cls", [MemoryRunPersister, db_persister])
@pytest.mark.asyncio
async def test_get_runs(cls):
    p = cls()
    await p.connect()
    await p.add_run(Run("stopped", Status.Success, start="2010-01-01"))
    await p.add_run(Run("running too", Status.Running, start="2015-01-01"))
    await p.add_run(Run("running", Status.Running, start="2019-01-01"))
    assert len(await p.get_runs()) == 3
    # status param
    assert len(await p.get_runs(status=Status.Running)) == 2
    assert len(await p.get_runs(status=[Status.Running, Status.Success])) == 3
    # task_name param
    assert len(await p.get_runs(task_name="stopped")) == 1
    assert len(await p.get_runs(task_name="empty")) == 0
    # check ordering
    assert [r.task for r in await p.get_runs()] == ["stopped", "running too", "running"]


@pytest.mark.parametrize("cls", [MemoryRunPersister, db_persister])
@pytest.mark.asyncio
async def test_get_runs_latest_n(cls):
    p = cls()
    await p.connect()
    await p.add_run(Run("one", Status.Success, start="2010-01-01"))
    await p.add_run(Run("two", Status.Running, start="2015-01-01"))
    await p.add_run(Run("three", Status.Running, start="2019-01-01"))

    # latest param
    latest_one = await p.get_runs(latest=1)
    assert len(latest_one) == 1
    assert latest_one[0].task == "three"

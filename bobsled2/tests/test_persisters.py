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
    await p.add_run(Run("running", Status.Running))
    await p.add_run(Run("running too", Status.Running))
    await p.add_run(Run("stopped", Status.Success))
    assert len(await p.get_runs()) == 3
    assert len(await p.get_runs(status=Status.Running)) == 2
    assert len(await p.get_runs(task_name="stopped")) == 1
    assert len(await p.get_runs(task_name="empty")) == 0

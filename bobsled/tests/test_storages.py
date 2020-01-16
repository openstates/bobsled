import os
import inspect
import pytest
from ..storages import InMemoryStorage, DatabaseStorage
from ..base import Run, Status, Task, Trigger


def db_storage():
    try:
        os.remove("test.db")
    except OSError:
        pass
    db = DatabaseStorage("sqlite:///test.db")
    return db


@pytest.mark.parametrize("Cls", [InMemoryStorage, DatabaseStorage])
def test_environment_settings_args(Cls):
    settings = Cls.ENVIRONMENT_SETTINGS.values()
    params = inspect.signature(Cls.__init__).parameters.keys()
    assert set(settings) == (set(params) - {"self"})


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
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


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
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


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
@pytest.mark.asyncio
async def test_bad_get(cls):
    p = cls()
    await p.connect()
    r = await p.get_run("nonsense")
    assert r is None


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
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


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
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


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
@pytest.mark.asyncio
async def test_task_storage(cls):
    s = cls()
    await s.connect()
    tasks = [
        Task(
            name="one",
            image="img1",
            tags=["yellow", "green"],
            entrypoint="entrypoint",
            environment="envname",
            memory=1024,
            cpu=512,
            enabled=False,
            timeout_minutes=60,
            triggers=[Trigger(cron="@daily")],
        ),
        Task(name="two", image="img2"),
    ]
    await s.set_tasks(tasks)

    retr_tasks = await s.get_tasks()
    # order-indepdendent comparison
    assert [t.name for t in retr_tasks] == ["one", "two"]
    task = await s.get_task("one")
    assert task == tasks[0]


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
@pytest.mark.asyncio
async def test_task_storage_updates(cls):
    s = cls()
    await s.connect()
    tasks = [Task(name="one", image="img1"), Task(name="two", image="img2")]
    await s.set_tasks(tasks)

    tasks = [Task(name="one", image="newimg"), Task(name="three", image="img3")]
    await s.set_tasks(tasks)
    retr_tasks = await s.get_tasks()
    # order-indepdendent comparison
    assert len(retr_tasks) == 2
    assert {t.name for t in retr_tasks} == {"one", "three"}
    task = await s.get_task("one")
    assert task == tasks[0]


@pytest.mark.parametrize("cls", [InMemoryStorage, db_storage])
@pytest.mark.asyncio
async def test_user_storage(cls):
    s = cls()
    await s.connect()
    # non-existent user
    check = await s.check_password("someone", "abc")
    assert not check
    # wrong password
    await s.set_password("someone", "xyz")
    check = await s.check_password("someone", "abc")
    assert not check
    # right password
    check = await s.check_password("someone", "xyz")
    assert check

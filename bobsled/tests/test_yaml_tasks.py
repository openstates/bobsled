import os
import pytest
from ..storages import InMemoryStorage
from ..tasks import YamlTaskProvider

ENV_FILE = os.path.join(os.path.dirname(__file__), "tasks/tasks.yml")
GH_API_KEY = os.environ.get("GITHUB_API_KEY")


@pytest.mark.asyncio
async def test_get_tasks():
    tp = YamlTaskProvider(storage=InMemoryStorage(), filename=ENV_FILE)
    await tp.update_tasks()
    tasks = await tp.get_tasks()
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_get_task():
    tp = YamlTaskProvider(storage=InMemoryStorage(), filename=ENV_FILE)
    await tp.update_tasks()
    task = await tp.get_task("full-example")
    assert task.name == "full-example"
    assert task.tags == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_get_tasks_github():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    tp = YamlTaskProvider(
        storage=InMemoryStorage(),
        filename="bobsled/tests/tasks/tasks.yml",
        github_user="jamesturk",
        github_repo="bobsled",
        github_api_key=GH_API_KEY,
    )
    await tp.update_tasks()
    tasks = await tp.get_tasks()
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_get_tasks_github_dir():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    tp = YamlTaskProvider(
        storage=InMemoryStorage(),
        github_user="jamesturk",
        github_repo="bobsled",
        dirname="bobsled/tests/tasks",
        github_api_key=GH_API_KEY,
    )
    tasks = await tp.update_tasks()
    tasks = await tp.get_tasks()
    assert len(tasks) == 4

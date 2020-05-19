import os
import pytest
from ..storages import InMemoryStorage
from ..tasks import TaskProvider

ENV_FILE = os.path.join(os.path.dirname(__file__), "tasks/tasks.yml")
GH_API_KEY = os.environ.get("GITHUB_API_KEY")


@pytest.mark.asyncio
async def test_basic_tasks():
    storage = InMemoryStorage()
    tp = TaskProvider(storage=storage, BOBSLED_TASKS_FILENAME=ENV_FILE)
    await tp.update_tasks()
    tasks = await storage.get_tasks()
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_load_github_tasks():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    storage = InMemoryStorage()
    tp = TaskProvider(
        storage=storage,
        BOBSLED_TASKS_FILENAME="bobsled/tests/tasks/tasks.yml",
        BOBSLED_CONFIG_GITHUB_USER="stateautomata",
        BOBSLED_CONFIG_GITHUB_REPO="bobsled",
        BOBSLED_GITHUB_API_KEY=GH_API_KEY,
    )
    await tp.update_tasks()
    tasks = await storage.get_tasks()
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_load_github_dir():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    storage = InMemoryStorage()
    tp = TaskProvider(
        storage=storage,
        BOBSLED_TASKS_DIRNAME="bobsled/tests/tasks/",
        BOBSLED_CONFIG_GITHUB_USER="stateautomata",
        BOBSLED_CONFIG_GITHUB_REPO="bobsled",
        BOBSLED_GITHUB_API_KEY=GH_API_KEY,
    )
    await tp.update_tasks()
    tasks = await storage.get_tasks()
    assert len(tasks) == 4

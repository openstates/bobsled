import os
import pytest
from ..storages import InMemoryStorage
from ..yaml_tasks import YamlTaskProvider

ENV_FILE = os.path.join(os.path.dirname(__file__), "tasks/tasks.yml")
GH_API_KEY = os.environ.get("GITHUB_API_KEY")


@pytest.mark.asyncio
async def test_basic_tasks():
    storage = InMemoryStorage()
    tp = YamlTaskProvider(storage=storage, BOBSLED_TASKS_FILENAME=ENV_FILE)
    tasks = await tp.update_tasks()
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_load_github_tasks():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    storage = InMemoryStorage()
    tp = YamlTaskProvider(
        storage=storage,
        BOBSLED_TASKS_FILENAME="bobsled/tests/tasks/tasks.yml",
        BOBSLED_CONFIG_GITHUB_USER="stateautomata",
        BOBSLED_CONFIG_GITHUB_REPO="bobsled",
        BOBSLED_GITHUB_API_KEY=GH_API_KEY,
    )
    tasks = await tp.update_tasks()
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_load_github_dir():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    tp = YamlTaskProvider(
        storage=InMemoryStorage(),
        BOBSLED_TASKS_DIRNAME="bobsled/tests/tasks/",
        BOBSLED_CONFIG_GITHUB_USER="stateautomata",
        BOBSLED_CONFIG_GITHUB_REPO="bobsled",
        BOBSLED_GITHUB_API_KEY=GH_API_KEY,
    )
    tasks = await tp.update_tasks()
    assert len(tasks) == 4

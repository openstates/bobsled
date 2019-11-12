import os
import pytest
from ..tasks import YamlTaskStorage

ENV_FILE = os.path.join(os.path.dirname(__file__), "tasks/tasks.yml")
GH_API_KEY = os.environ.get("GITHUB_API_KEY")


def test_get_tasks():
    tasks = YamlTaskStorage(filename=ENV_FILE)
    assert len(tasks.get_tasks()) == 3


def test_get_task():
    tasks = YamlTaskStorage(filename=ENV_FILE)
    task = tasks.get_task("full-example")
    assert task.name == "full-example"
    assert task.tags == ["a", "b", "c"]


def test_get_tasks_github():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    tasks = YamlTaskStorage(
        filename="bobsled/tests/tasks/tasks.yml",
        github_user="jamesturk",
        github_repo="bobsled",
        github_api_key=GH_API_KEY,
    )
    assert len(tasks.get_tasks()) == 3


def test_get_tasks_github_dir():
    if not GH_API_KEY:
        pytest.skip("no GitHub API Key")
    tasks = YamlTaskStorage(
        github_user="jamesturk",
        github_repo="bobsled",
        dirname="bobsled/tests/tasks",
        github_api_key=GH_API_KEY,
    )
    assert len(tasks.get_tasks()) == 4

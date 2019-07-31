import os
from ..tasks import YamlTaskStorage

ENV_FILE = os.path.join(os.path.dirname(__file__), "tasks.yml")


def test_get_tasks():
    tasks = YamlTaskStorage(ENV_FILE)
    assert len(tasks.get_tasks()) == 3


def test_get_task():
    tasks = YamlTaskStorage(ENV_FILE)
    task = tasks.get_task("full-example")
    assert task.name == "full-example"
    assert task.tags == ["a", "b", "c"]

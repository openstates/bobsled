import os
from ..yaml_tasks import YamlTasks, Task

ENV_FILE = os.path.join(os.path.dirname(__file__), "tasks.yml")

def test_get_tasks():
    tasks = YamlTasks(ENV_FILE)
    assert tasks.get_tasks() == ["hello-world", "full-example"]

def test_get_task():
    tasks = YamlTasks(ENV_FILE)
    task = tasks.get_task("full-example")
    assert task.name == "full-example"
    assert task.tags == ["a", "b", "c"]

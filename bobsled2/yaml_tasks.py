import yaml
from .base import Task, TaskService


class YamlTasks(TaskService):
    def __init__(self, filename):
        with open(filename) as f:
            data = yaml.safe_load(f)
        self.tasks = {}
        for name, taskdef in data.items():
            self.tasks[name] = Task(name=name, **taskdef)

    def get_tasks(self):
        return list(self.tasks.keys())

    def get_task(self, name):
        return self.tasks[name]

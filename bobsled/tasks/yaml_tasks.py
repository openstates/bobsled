import yaml
import github3
from ..base import Task


class YamlTaskStorage:
    def __init__(self, filename, github_user=None, github_repo=None):
        if github_user and github_repo:
            gh = github3.GitHub()
            repo = gh.repository(github_user, github_repo)
            contents = repo.file_contents(filename).decoded
            data = yaml.safe_load(contents)
        else:
            with open(filename) as f:
                data = yaml.safe_load(f)
        self.tasks = {}
        for name, taskdef in data.items():
            self.tasks[name] = Task(name=name, **taskdef)

    def get_tasks(self):
        return list(self.tasks.values())

    def get_task(self, name):
        return self.tasks[name]

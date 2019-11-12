import yaml
import github3
from ..base import Task


class YamlTaskStorage:
    def __init__(
        self,
        *,
        filename=None,
        github_user=None,
        github_repo=None,
        dirname=None,
        github_api_key=None,
    ):
        if github_user and github_repo:
            gh = github3.GitHub(token=github_api_key)
            repo = gh.repository(github_user, github_repo)
            if filename:
                contents = repo.file_contents(filename).decoded
                data = yaml.safe_load(contents)
            elif dirname:
                data = {}
                for fname, contents in repo.directory_contents(dirname):
                    contents.refresh()
                    data.update(yaml.safe_load(contents.decoded))
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

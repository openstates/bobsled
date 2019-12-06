import yaml
import github3
from ..base import Task, TaskProvider


class YamlTaskProvider(TaskProvider):
    def __init__(
        self,
        *,
        storage,
        filename=None,
        github_user=None,
        github_repo=None,
        dirname=None,
        github_api_key=None,
    ):
        self.storage = storage
        self.filename = filename
        self.github_user = github_user
        self.github_repo = github_repo
        self.dirname = dirname
        self.github_api_key = github_api_key

    async def update_tasks(self):
        if self.github_user and self.github_repo:
            gh = github3.GitHub(token=self.github_api_key)
            repo = gh.repository(self.github_user, self.github_repo)
            if self.filename:
                contents = repo.file_contents(self.filename).decoded
                data = yaml.safe_load(contents)
            elif self.dirname:
                data = {}
                for fname, contents in repo.directory_contents(self.dirname):
                    contents.refresh()
                    data.update(yaml.safe_load(contents.decoded))
        else:
            with open(self.filename) as f:
                data = yaml.safe_load(f)

        tasks = [Task(name=name, **taskdef) for name, taskdef in data.items()]
        await self.storage.set_tasks(tasks)

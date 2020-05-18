import glob
import yaml
import github3
from ..base import Task, TaskProvider, Trigger


class YamlTaskProvider(TaskProvider):
    def __init__(
        self,
        *,
        storage,
        BOBSLED_TASKS_FILENAME=None,
        BOBSLED_TASKS_GITHUB_USER=None,
        BOBSLED_TASKS_GITHUB_REPO=None,
        BOBSLED_TASKS_DIRNAME=None,
        BOBSLED_GITHUB_API_KEY=None,
    ):
        self.storage = storage
        self.filename = BOBSLED_TASKS_FILENAME
        self.github_user = BOBSLED_TASKS_GITHUB_USER
        self.github_repo = BOBSLED_TASKS_GITHUB_REPO
        self.dirname = BOBSLED_TASKS_DIRNAME
        self.github_api_key = BOBSLED_GITHUB_API_KEY

        if not self.filename and not self.dirname:
            raise EnvironmentError(
                "must provide either BOBSLED_TASKS_FILENAME or BOBSLED_TASKS_DIRNAME"
            )

    async def update_tasks(self):
        if self.github_user and self.github_repo:
            gh = github3.GitHub(token=self.github_api_key)
            repo = gh.repository(self.github_user, self.github_repo)
            if self.dirname:
                data = {}
                for fname, contents in repo.directory_contents(self.dirname):
                    contents.refresh()
                    data.update(yaml.safe_load(contents.decoded))
            elif self.filename:
                contents = repo.file_contents(self.filename).decoded
                data = yaml.safe_load(contents)
        elif self.dirname:
            data = {}
            for filename in glob.glob(self.dirname + "/*"):
                with open(filename) as f:
                    data.append(yaml.safe_load(f))
        else:
            with open(self.filename) as f:
                data = yaml.safe_load(f)

        tasks = [Task(name=name, **taskdef) for name, taskdef in data.items()]
        for task in tasks:
            task.triggers = [Trigger(**t) for t in task.triggers]
        await self.storage.set_tasks(tasks)

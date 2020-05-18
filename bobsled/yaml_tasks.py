from .base import Task, TaskProvider, Trigger
from .utils import load_github_or_local_yaml


class YamlTaskProvider(TaskProvider):
    def __init__(
        self,
        *,
        storage,
        BOBSLED_TASKS_FILENAME=None,
        BOBSLED_TASKS_DIRNAME=None,
        BOBSLED_CONFIG_GITHUB_USER=None,
        BOBSLED_CONFIG_GITHUB_REPO=None,
        BOBSLED_GITHUB_API_KEY=None,
    ):
        self.storage = storage
        self.filename = BOBSLED_TASKS_FILENAME
        self.dirname = BOBSLED_TASKS_DIRNAME
        self.github_user = BOBSLED_CONFIG_GITHUB_USER
        self.github_repo = BOBSLED_CONFIG_GITHUB_REPO
        self.github_api_key = BOBSLED_GITHUB_API_KEY

        if not self.filename and not self.dirname:
            raise EnvironmentError(
                "must provide either BOBSLED_TASKS_FILENAME or BOBSLED_TASKS_DIRNAME"
            )

    async def update_tasks(self):
        data = load_github_or_local_yaml(
            self.filename,
            self.dirname,
            self.github_user,
            self.github_repo,
            self.github_api_key,
        )
        tasks = [Task(name=name, **taskdef) for name, taskdef in data.items()]
        for task in tasks:
            task.triggers = [Trigger(**t) for t in task.triggers]
        await self.storage.set_tasks(tasks)

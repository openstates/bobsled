import os
import asyncio
from bobsled import storages, runners, callbacks
from bobsled.yaml_environment import YamlEnvironmentProvider
from bobsled.yaml_tasks import YamlTaskProvider
from bobsled.utils import get_env_config, load_args


class Bobsled:
    def __init__(self):
        self.settings = {"secret_key": os.environ.get("BOBSLED_SECRET_KEY", None)}
        if self.settings["secret_key"] is None:
            raise ValueError("must set 'secret_key' setting")

        # env and task providers can't currently be overriden
        env_args = load_args(YamlEnvironmentProvider)
        task_args = load_args(YamlTaskProvider)
        # storage and run are overridable
        StorageCls, storage_args = get_env_config(
            "BOBSLED_STORAGE", "InMemoryStorage", storages
        )
        RunCls, run_args = get_env_config("BOBSLED_RUNNER", "LocalRunService", runners)

        callback_classes = []
        if os.environ.get("BOBSLED_ENABLE_GITHUB_ISSUE_CALLBACK"):
            CallbackCls = callbacks.GithubIssueCallback
            callback_classes.append(CallbackCls(**load_args(CallbackCls)))

        self.storage = StorageCls(**storage_args)
        self.env = YamlEnvironmentProvider(**env_args)
        self.tasks = YamlTaskProvider(storage=self.storage, **task_args)
        self.run = RunCls(
            storage=self.storage,
            environment=self.env,
            callbacks=callback_classes,
            **run_args,
        )

    async def initialize(self):
        await self.storage.connect()
        tasks = await self.tasks.get_tasks()
        if not tasks:
            await self.refresh_config()
        else:
            self.run.initialize(tasks)

    async def refresh_config(self):
        await asyncio.gather(
            self.tasks.update_tasks(), self.environment.update_environments()
        )
        tasks = await self.tasks.get_tasks()
        self.run.initialize(tasks)
        return tasks


bobsled = Bobsled()

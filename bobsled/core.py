import os
from bobsled import storages, environments, tasks, runners, callbacks
from bobsled.utils import get_env_config, load_args


class Bobsled:
    def __init__(self):
        self.settings = {"secret_key": os.environ.get("BOBSLED_SECRET_KEY", None)}
        if self.settings["secret_key"] is None:
            raise ValueError("must set 'secret_key' setting")

        EnvCls, env_args = get_env_config(
            "BOBSLED_ENVIRONMENT_PROVIDER", "LocalEnvironmentProvider", environments
        )
        StorageCls, storage_args = get_env_config(
            "BOBSLED_STORAGE", "InMemoryStorage", storages
        )
        TaskCls, task_args = get_env_config(
            "BOBSLED_TASK_PROVIDER", "YamlTaskProvider", tasks
        )
        RunCls, run_args = get_env_config("BOBSLED_RUNNER", "LocalRunService", runners)

        callback_classes = []
        if os.environ.get("BOBSLED_ENABLE_GITHUB_ISSUE_CALLBACK"):
            CallbackCls = callbacks.GithubIssueCallback
            callback_classes.append(CallbackCls(**load_args(CallbackCls)))

        self.storage = StorageCls(**storage_args)
        self.env = EnvCls(**env_args)
        self.tasks = TaskCls(storage=self.storage, **task_args)
        self.run = RunCls(
            storage=self.storage,
            environment=self.env,
            callbacks=callback_classes,
            **run_args,
        )

    async def initialize(self):
        await self.storage.connect()
        await self.tasks.update_tasks()
        tasks = await bobsled.tasks.get_tasks()
        self.run.initialize(tasks)


bobsled = Bobsled()

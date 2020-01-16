import os
import json

from bobsled import storages, environments, tasks, runners, callbacks


def get_env_json(key, default):
    val = os.environ.get(key, None)
    if not val:
        return default
    else:
        return json.loads(val)


class Bobsled:
    def __init__(self):
        self.settings = {"secret_key": os.environ.get("BOBSLED_SECRET_KEY", None)}
        if self.settings["secret_key"] is None:
            raise ValueError("must set 'secret_key' setting")

        storage_cfg = get_env_json(
            "BOBSLED_STORAGE", {"provider": "InMemoryStorage", "args": {}}
        )
        env_cfg = get_env_json(
            "BOBSLED_ENVIRONMENTS",
            {"provider": "LocalEnvironmentProvider", "args": {"environments": {}}},
        )
        task_cfg = get_env_json(
            "BOBSLED_TASKS",
            {"provider": "YamlTaskProvider", "args": {"filename": "tasks.yml"}},
        )
        run_cfg = get_env_json(
            "BOBSLED_RUNNER", {"provider": "LocalRunService", "args": {}}
        )

        EnvCls = getattr(environments, env_cfg["provider"])
        TaskCls = getattr(tasks, task_cfg["provider"])
        RunCls = getattr(runners, run_cfg["provider"])
        StorageCls = getattr(storages, storage_cfg["provider"])

        callback_classes = []
        for cb in get_env_json("BOBSLED_CALLBACKS", []):
            PluginCls = getattr(callbacks, cb["plugin"])
            callback_classes.append(PluginCls(**cb["args"]))

        self.storage = StorageCls(**storage_cfg["args"])
        self.env = EnvCls(**env_cfg["args"])
        self.tasks = TaskCls(storage=self.storage, **task_cfg["args"])
        self.run = RunCls(
            storage=self.storage,
            environment=self.env,
            callbacks=callback_classes,
            **run_cfg["args"]
        )

    async def initialize(self):
        await self.storage.connect()
        await self.tasks.update_tasks()
        tasks = await bobsled.tasks.get_tasks()
        self.run.initialize(tasks)


bobsled = Bobsled()

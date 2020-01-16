import os

from bobsled import storages, environments, tasks, runners  # , callbacks


def get_env_config(key, default, module):
    """
    Get class configuration from the environment.

    Reads the environment variable 'key', and loads the appropriate class from 'module'.

    Then inspects the class and finds out what additional variables need to be loaded via
    Cls.ENVIRONMENT_SETTINGS
    """
    name = os.environ.get(key, default)
    Cls = getattr(module, name)

    env_cfg = getattr(Cls, "ENVIRONMENT_SETTINGS", {})
    args = {}
    for env_var_name, arg_name in env_cfg.items():
        args[arg_name] = os.environ[env_var_name]

    return Cls, args


class Bobsled:
    def __init__(self):
        self.settings = {"secret_key": os.environ.get("BOBSLED_SECRET_KEY", None)}
        if self.settings["secret_key"] is None:
            raise ValueError("must set 'secret_key' setting")

        EnvCls, env_args = get_env_config(
            "BOBSLED_ENV_PROVIDER", "LocalEnvironmentProvider", environments
        )
        StorageCls, storage_args = get_env_config(
            "BOBSLED_STORAGE_PROVIDER", "InMemoryStorage", storages
        )
        TaskCls, task_args = get_env_config(
            "BOBSLED_TASK_PROVIDER", "YamlTaskProvider", tasks
        )
        RunCls, run_args = get_env_config("BOBSLED_RUNNER", "LocalRunService", runners)

        # callback_classes = []
        # for cb in get_env_json("BOBSLED_CALLBACKS", []):
        #     PluginCls = getattr(callbacks, cb["plugin"])
        #     callback_classes.append(PluginCls(**cb["args"]))

        self.storage = StorageCls(**storage_args)
        self.env = EnvCls(**env_args)
        self.tasks = TaskCls(storage=self.storage, **task_args)
        self.run = RunCls(
            storage=self.storage,
            environment=self.env,
            # callbacks=callback_classes,
            **run_args,
        )

    async def initialize(self):
        await self.storage.connect()
        await self.tasks.update_tasks()
        tasks = await bobsled.tasks.get_tasks()
        self.run.initialize(tasks)


bobsled = Bobsled()

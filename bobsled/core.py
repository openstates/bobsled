import os
import copy
import yaml

from bobsled import environments, tasks, runners, auth

DEFAULT_SETTINGS = {
    "environments": {
        "provider": "YamlEnvironmentStorage",
        "args": {"filename": "environments.yml"},
    },
    "tasks": {"provider": "YamlTaskStorage", "args": {"filename": "tasks.yml"}},
    "runner": {"provider": "LocalRunService", "args": {}},
    "persister": {"provider": "MemoryRunPersister", "args": {}},
    "auth": {"provider": "YamlAuthStorage", "args": {"filename": "users.yml"}},
    "on_error": [{"callback": "github_on_error"}],
    "on_success": [],
    "secret_key": None,
}


class Bobsled:
    def __init__(self):
        filename = os.environ.get("BOBSLED_SETTINGS_FILE", "bobsled.yml")
        with open(filename) as f:
            settings = copy.deepcopy(DEFAULT_SETTINGS)
            settings.update(yaml.safe_load(f))

        if settings["secret_key"] is None:
            raise ValueError("must set 'secret_key' setting")
        self.settings = settings

        EnvCls = getattr(environments, settings["environments"]["provider"])
        TaskCls = getattr(tasks, settings["tasks"]["provider"])
        RunCls = getattr(runners, settings["runner"]["provider"])
        PersisterCls = getattr(runners, settings["persister"]["provider"])
        AuthCls = getattr(auth, settings["auth"]["provider"])

        self.env = EnvCls(**settings["environments"]["args"])
        self.tasks = TaskCls(**settings["tasks"]["args"])
        self.run = RunCls(
            persister=PersisterCls(**settings["persister"]["args"]),
            environment=self.env,
            **settings["runner"]["args"]
        )
        self.auth = AuthCls(**settings["auth"]["args"])
        self.run.initialize(self.tasks.get_tasks())


bobsled = Bobsled()

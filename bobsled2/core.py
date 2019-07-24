import os
import copy
import importlib
import yaml

from bobsled2 import environments, tasks, runners

DEFAULT_SETTINGS = {
    "environments": {
        "provider": "YamlEnvironmentStorage",
        "args": {
            "filename": "environments.yml",
        },
    },
    "tasks": {
        "provider": "YamlTaskStorage",
        "args": {
            "filename": "tasks.yml",
        }
    },
    "runner": {
        "provider": "LocalRunService",
        "args": {
        }
    },
    "persister": {
        "provider": "DatabaseRunPersister",
        "args": {
            "database_uri": "sqlite:///bobsled2.db",
        }
    }
}


class Bobsled:
    def __init__(self):
        filename = os.environ.get("BOBSLED_SETTINGS_FILE", "bobsled.yml")
        with open(filename) as f:
            settings = copy.deepcopy(DEFAULT_SETTINGS)
            settings.update(yaml.safe_load(f))

        EnvCls = getattr(environments, settings["environments"]["provider"])
        TaskCls = getattr(tasks, settings["tasks"]["provider"])
        RunCls = getattr(runners, settings["runner"]["provider"])
        PersisterCls = getattr(runners, settings["persister"]["provider"])

        self.env = EnvCls(**settings["environments"]["args"])
        self.tasks = TaskCls(**settings["tasks"]["args"])
        self.run = RunCls(persister=PersisterCls(**settings["persister"]["args"]),
                          **settings["runner"]["args"])

bobsled = Bobsled()

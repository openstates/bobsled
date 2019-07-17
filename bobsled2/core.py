import os
import importlib

settings = importlib.import_module(os.environ.get("BOBSLED_SETTINGS_MODULE", "bobsled_settings"))

class Bobsled:
    def __init__(self):
        self.env = settings.ENVIRONMENT_SERVICE
        self.tasks = settings.TASK_SERVICE
        self.run = settings.RUN_SERVICE

bobsled = Bobsled()

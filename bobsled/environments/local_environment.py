from ..base import Environment, EnvironmentProvider
import json


class LocalEnvironmentProvider(EnvironmentProvider):
    def __init__(self, BOBSLED_ENVIRONMENT_JSON="{}"):
        self.environments = {}
        env = json.loads(BOBSLED_ENVIRONMENT_JSON)
        for name, values in env.items():
            self.environments[name] = Environment(name, values)

    def get_environment_names(self):
        return list(self.environments.keys())

    def get_environment(self, name):
        return self.environments[name]

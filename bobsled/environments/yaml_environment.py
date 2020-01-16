import yaml
from ..base import Environment, EnvironmentProvider


class YamlEnvironmentProvider(EnvironmentProvider):
    def __init__(self, BOBSLED_ENVIRONMENT_FILENAME):
        with open(BOBSLED_ENVIRONMENT_FILENAME) as f:
            data = yaml.safe_load(f)
        self.environments = {}
        for name, values in data.items():
            self.environments[name] = Environment(name, values)

    def get_environment_names(self):
        return list(self.environments.keys())

    def get_environment(self, name):
        return self.environments[name]

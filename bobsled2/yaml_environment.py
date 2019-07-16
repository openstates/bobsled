from .base import EnvironmentService, Environment
import yaml


class YamlEnvironment:
    def __init__(self, filename):
        with open(filename) as f:
            data = yaml.safe_load(f)
        self.environments = {}
        for name, values in data.items():
            self.environments[name] = Environment(name, values)

    def get_environments(self):
        return list(self.environments.keys())

    def get_environment(self, name):
        return self.environments[name]

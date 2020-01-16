from ..base import Environment, EnvironmentProvider


class LocalEnvironmentProvider(EnvironmentProvider):
    def __init__(self, BOBSLED_ENVIRONMENT_JSON):
        self.environments = {}
        for name, values in BOBSLED_ENVIRONMENT_JSON.items():
            self.environments[name] = Environment(name, values)

    def get_environment_names(self):
        return list(self.environments.keys())

    def get_environment(self, name):
        return self.environments[name]

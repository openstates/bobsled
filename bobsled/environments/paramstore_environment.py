import boto3
from ..base import Environment, EnvironmentProvider


def get_all_ssm_parameters(path):
    ssm = boto3.client("ssm")
    resp = ssm.get_parameters_by_path(Path=path, WithDecryption=True, Recursive=True)
    yield from resp["Parameters"]

    while True:
        try:
            next_token = resp["NextToken"]
        except KeyError:
            break

        resp = ssm.get_parameters_by_path(
            Path=path, WithDecryption=True, Recursive=True, NextToken=next_token
        )
        yield from resp["Parameters"]


class ParameterStoreEnvironmentProvider(EnvironmentProvider):
    def __init__(self, BOBSLED_ENVIRONMENT_PARAMSTORE_PREFIX):
        self.prefix = BOBSLED_ENVIRONMENT_PARAMSTORE_PREFIX

    def get_environment_names(self):
        names = set()
        for param in get_all_ssm_parameters(self.prefix):
            env, _ = param["Name"].replace(self.prefix, "").lstrip("/").split("/")
            names.add(env)
        return list(names)

    def get_environment(self, name):
        env = {}
        for param in get_all_ssm_parameters(self.prefix + "/" + name):
            _, _, _, key = param["Name"].split("/", 4)
            value = param["Value"]
            env[key] = value
        return Environment(name, env)

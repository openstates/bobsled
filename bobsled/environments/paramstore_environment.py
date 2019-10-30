from collections import defaultdict
import boto3
from ..base import Environment, EnvironmentStorage


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


class ParameterStoreEnvironmentStorage(EnvironmentStorage):
    def __init__(self, prefix):
        self.prefix = prefix
        envs = defaultdict(dict)
        for param in get_all_ssm_parameters(prefix):
            env, key = param["Name"].replace(prefix, "").lstrip("/").split("/")
            value = param["Value"]
            envs[env][key] = value

        self.environments = {}
        for name, values in envs.items():
            self.environments[name] = Environment(name, values)

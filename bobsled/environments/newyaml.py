import yaml
import boto3
from ..base import Environment, EnvironmentProvider

"""
Format of environment file:

<environment_name>:
    - variable: <variable_name>
      hidden: [true|false]
      paramstore: <paramstore path>
           OR
      string: <value>
"""


def paramstore_loader(varname):
    ssm = boto3.client("ssm")
    resp = ssm.get_parameter(Name=varname, WithDecryption=True)
    return resp["Parameter"]["Value"]


class YamlEnvironmentProvider(EnvironmentProvider):
    def __init__(self, BOBSLED_ENVIRONMENT_FILENAME):
        self.filename = BOBSLED_ENVIRONMENT_FILENAME
        self.environments = {}

    def get_environment_names(self):
        return list(self.environments.keys())

    def get_environment(self, name):
        return self.environments[name]

    async def update_environments(self):
        with open(self.filename) as f:
            data = yaml.safe_load(f)

        for name, envdef in data.items():
            values = {}
            for env_var in envdef:
                if "string" in env_var:
                    values[env_var["variable"]] = env_var["string"]
                elif "paramstore" in env_var:
                    values[env_var["variable"]] = paramstore_loader(
                        env_var["paramstore"]
                    )
                else:
                    raise ValueError(
                        f"{name}.{env_var['variable']} must include 'string' or 'paramstore'"
                    )
            self.environments[name] = Environment(name, values)

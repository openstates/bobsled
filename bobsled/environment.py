import boto3
from .base import Environment
from .utils import load_github_or_local_yaml

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


class EnvironmentProvider:
    def __init__(
        self,
        BOBSLED_ENVIRONMENT_FILENAME=None,
        BOBSLED_ENVIRONMENT_DIRNAME=None,
        BOBSLED_CONFIG_GITHUB_USER=None,
        BOBSLED_CONFIG_GITHUB_REPO=None,
        BOBSLED_GITHUB_API_KEY=None,
    ):
        self.filename = BOBSLED_ENVIRONMENT_FILENAME
        self.dirname = BOBSLED_ENVIRONMENT_DIRNAME
        self.github_user = BOBSLED_CONFIG_GITHUB_USER
        self.github_repo = BOBSLED_CONFIG_GITHUB_REPO
        self.github_api_key = BOBSLED_GITHUB_API_KEY
        self.environments = {}

        if not self.filename and not self.dirname:
            raise EnvironmentError(
                "must provide either BOBSLED_ENVIRONMENT_FILENAME or BOBSLED_ENVIRONMENT_DIRNAME"
            )

    def mask_variables(self, string):
        for env_name in self.get_environment_names():
            env = self.get_environment(env_name)
            for var, value in env.values.items():
                string = string.replace(
                    str(value), f"**{env_name.upper()}/{var.upper()}**"
                )
        return string

    def get_environment_names(self):
        return list(self.environments.keys())

    def get_environment(self, name):
        return self.environments[name]

    async def update_environments(self):
        data = load_github_or_local_yaml(
            self.filename,
            self.dirname,
            self.github_user,
            self.github_repo,
            self.github_api_key,
        )

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

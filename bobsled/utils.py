import os
import inspect
import glob
import yaml
import github3
from passlib.hash import argon2


def verify_password(password, password_hash):
    return argon2.verify(password, password_hash)


def hash_password(password):
    return argon2.hash(password)


def load_args(Cls):
    """
    Parameters that start with BOBSLED_ are read from environment & returned as kwargs.
    """
    signature = [
        p
        for p in inspect.signature(Cls.__init__).parameters.values()
        if p.name.startswith("BOBSLED_")
    ]
    args = {}
    for arg in signature:
        if arg.name not in os.environ and arg.default == arg.empty:
            raise EnvironmentError(
                f"{Cls} requires {arg.name} to be set in the environment"
            )
        elif arg.name in os.environ:
            args[arg.name] = os.environ[arg.name]
    return args


def get_env_config(key, default, module):
    """
    Get class configuration from the environment.

    Reads the environment variable 'key', and loads the appropriate class from 'module'.

    Then pulls args from load_args
    """
    name = os.environ.get(key, default)
    Cls = getattr(module, name)
    args = load_args(Cls)
    return Cls, args


def load_github_or_local_yaml(
    filename, dirname, github_user=None, github_repo=None, github_api_key=None
):
    """
    load_yaml from a local or remote source

    if github credentials are supplied, they'll be used and we'll read from the directory or
    file within the repo

    otherwise, the local file will be used
    """
    if github_user and github_repo:
        gh = github3.GitHub(token=github_api_key)
        repo = gh.repository(github_user, github_repo)
        if dirname:
            data = {}
            for fname, contents in repo.directory_contents(dirname):
                contents.refresh()
                data.update(yaml.safe_load(contents.decoded))
        elif filename:
            contents = repo.file_contents(filename).decoded
            data = yaml.safe_load(contents)
    elif dirname:
        data = {}
        for filename in glob.glob(dirname + "/*"):
            with open(filename) as f:
                data.append(yaml.safe_load(f))
    else:
        with open(filename) as f:
            data = yaml.safe_load(f)

    return data

import os
import inspect
from passlib.hash import argon2


def verify_password(password, password_hash):
    return argon2.verify(password, password_hash)


def hash_password(password):
    return argon2.hash(password)


def get_env_config(key, default, module):
    """
    Get class configuration from the environment.

    Reads the environment variable 'key', and loads the appropriate class from 'module'.

    Then inspects the class and finds out what additional variables need to be loaded via
    Cls.ENVIRONMENT_SETTINGS
    """
    name = os.environ.get(key, default)
    Cls = getattr(module, name)

    arg_names = [
        p
        for p in inspect.signature(Cls.__init__).parameters
        if p.startswith("BOBSLED_")
    ]
    args = {arg_name: os.environ[arg_name] for arg_name in arg_names}

    return Cls, args

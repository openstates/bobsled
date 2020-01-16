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
    return Cls, args

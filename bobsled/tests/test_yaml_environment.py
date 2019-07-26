import os
from ..environments import YamlEnvironmentStorage
from ..base import Environment

ENV_FILE = os.path.join(os.path.dirname(__file__), "testenv.yml")

def test_get_environments():
    env = YamlEnvironmentStorage(ENV_FILE)
    assert len(env.get_environments()) == 2


def test_environment():
    env = YamlEnvironmentStorage(ENV_FILE)
    assert env.get_environment("one") == Environment("one", {"number": 123, "word": "hello"})

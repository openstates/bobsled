import os
from ..yaml_environment import YamlEnvironment, Environment

ENV_FILE = os.path.join(os.path.dirname(__file__), "testenv.yml")

def test_get_environments():
    env = YamlEnvironment(ENV_FILE)
    assert env.get_environments() == ["one", "two"]


def test_environment():
    env = YamlEnvironment(ENV_FILE)
    assert env.get_environment("one") == Environment("one", {"number": 123, "word": "hello"})

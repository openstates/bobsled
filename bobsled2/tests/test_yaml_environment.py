import yaml
from ..yaml_environment import YamlEnvironment, Environment

def setup():
    with open("testenv.yml", "w") as f:
        yaml.dump({
            "one": {"number": 123, "word": "hello"},
            "two": {"foo": "bar"},
        },
                  f)


def test_get_environments():
    env = YamlEnvironment("testenv.yml")
    assert env.get_environments() == ["one", "two"]


def test_environment():
    env = YamlEnvironment("testenv.yml")
    assert env.get_environment("one") == Environment("one", {"number": 123, "word": "hello"})

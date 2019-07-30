import os
import moto
import boto3
from ..environments import YamlEnvironmentStorage, ParameterStoreEnvironmentStorage
from ..base import Environment

ENV_FILE = os.path.join(os.path.dirname(__file__), "testenv.yml")


def test_get_environments_yaml():
    env = YamlEnvironmentStorage(ENV_FILE)
    assert len(env.get_environments()) == 2


def test_get_environment_yaml():
    env = YamlEnvironmentStorage(ENV_FILE)
    assert env.get_environment("one") == Environment("one", {"number": 123, "word": "hello"})


def _populate_paramstore():
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name="/bobsledtest/one/number", Value="123", Type="SecureString")
    ssm.put_parameter(Name="/bobsledtest/one/word", Value="hello", Type="SecureString")
    ssm.put_parameter(Name="/bobsledtest/two/foo", Value="bar", Type="SecureString")


@moto.mock_ssm
def test_get_environments_ssm():
    _populate_paramstore()
    env = ParameterStoreEnvironmentStorage("/bobsledtest")
    assert len(env.get_environments()) == 2


@moto.mock_ssm
def test_get_environment_ssm():
    _populate_paramstore()
    env = ParameterStoreEnvironmentStorage("/bobsledtest")
    assert env.get_environment("one") == Environment("one", {"number": "123", "word": "hello"})

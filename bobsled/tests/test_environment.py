import os
import moto
import boto3
from ..environments import YamlEnvironmentProvider, ParameterStoreEnvironmentProvider
from ..base import Environment

ENV_FILE = os.path.join(os.path.dirname(__file__), "environments.yml")


def test_get_environment_names_yaml():
    env = YamlEnvironmentProvider(ENV_FILE)
    assert len(env.get_environment_names()) == 2


def test_get_environment_yaml():
    env = YamlEnvironmentProvider(ENV_FILE)
    assert env.get_environment("one") == Environment(
        "one", {"number": 123, "word": "hello"}
    )


def test_mask_variables_yaml():
    env = YamlEnvironmentProvider(ENV_FILE)
    assert env.mask_variables("hello this is a test") == "**ONE/WORD** this is a test"


def _populate_paramstore():
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name="/bobsledtest/one/number", Value="123", Type="SecureString")
    ssm.put_parameter(Name="/bobsledtest/one/word", Value="hello", Type="SecureString")
    ssm.put_parameter(Name="/bobsledtest/two/foo", Value="bar", Type="SecureString")


@moto.mock_ssm
def test_get_environment_names_ssm():
    _populate_paramstore()
    env = ParameterStoreEnvironmentProvider("/bobsledtest")
    assert len(env.get_environment_names()) == 2


@moto.mock_ssm
def test_get_environment_ssm():
    _populate_paramstore()
    env = ParameterStoreEnvironmentProvider("/bobsledtest")
    assert env.get_environment("one") == Environment(
        "one", {"number": "123", "word": "hello"}
    )


@moto.mock_ssm
def test_get_environment_changes_ssm():
    _populate_paramstore()
    env = ParameterStoreEnvironmentProvider("/bobsledtest")
    assert env.get_environment("one") == Environment(
        "one", {"number": "123", "word": "hello"}
    )
    ssm = boto3.client("ssm")
    ssm.put_parameter(
        Name="/bobsledtest/one/number", Value="456", Type="SecureString", Overwrite=True
    )
    assert env.get_environment("one") == Environment(
        "one", {"number": "456", "word": "hello"}
    )


@moto.mock_ssm
def test_mask_variables_ssm():
    _populate_paramstore()
    env = ParameterStoreEnvironmentProvider("/bobsledtest")
    assert env.mask_variables("hello this is a test") == "**ONE/WORD** this is a test"

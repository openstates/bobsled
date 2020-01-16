import os
import pytest
from .. import storages, tasks
from bobsled.utils import get_env_config


def test_get_env_config_basic():
    os.environ["FAKE_TEST_KEY"] = "DatabaseStorage"
    os.environ["BOBSLED_DATABASE_URI"] = "test://"
    Cls, args = get_env_config("FAKE_TEST_KEY", None, storages)
    assert Cls is storages.DatabaseStorage
    assert args == {"BOBSLED_DATABASE_URI": "test://"}


def test_get_env_config_defaults():
    os.environ["FAKE_TEST_KEY"] = "YamlTaskProvider"
    os.environ["BOBSLED_TASKS_FILENAME"] = "foo"
    Cls, args = get_env_config("FAKE_TEST_KEY", None, tasks)
    assert Cls is tasks.YamlTaskProvider
    assert args == {"BOBSLED_TASKS_FILENAME": "foo"}


def test_get_env_config_missing():
    os.environ["FAKE_TEST_KEY"] = "DatabaseStorage"
    os.environ.pop("BOBSLED_DATABASE_URI", None)
    with pytest.raises(EnvironmentError):
        Cls, args = get_env_config("FAKE_TEST_KEY", None, storages)

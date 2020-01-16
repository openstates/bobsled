import os
import inspect
import pytest
from ..environments import (
    LocalEnvironmentProvider,
    YamlEnvironmentProvider,
    ParameterStoreEnvironmentProvider,
)
from .. import storages
from ..storages import InMemoryStorage, DatabaseStorage
from ..tasks import YamlTaskProvider
from ..runners import LocalRunService, ECSRunService
from bobsled.core import get_env_config


@pytest.mark.parametrize(
    "Cls,exclude",
    [
        (LocalEnvironmentProvider, set()),
        (YamlEnvironmentProvider, set()),
        (ParameterStoreEnvironmentProvider, set()),
        (InMemoryStorage, set()),
        (DatabaseStorage, set()),
        (YamlTaskProvider, {"storage"}),
        (LocalRunService, {"storage", "environment", "callbacks"}),
        (ECSRunService, {"storage", "environment", "callbacks"}),
    ],
)
def test_environment_settings_args(Cls, exclude):
    settings = Cls.ENVIRONMENT_SETTINGS.values()
    params = inspect.signature(Cls.__init__).parameters.keys()
    assert set(settings) == (set(params) - ({"self"} | exclude))


def test_get_env_config():
    os.environ["FAKE_TEST_KEY"] = "DatabaseStorage"
    Cls, args = get_env_config("FAKE_TEST_KEY", None, storages)
    assert Cls == DatabaseStorage
    assert args == {}

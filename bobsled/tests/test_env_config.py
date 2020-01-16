import os
from .. import storages
from bobsled.utils import get_env_config


def test_get_env_config():
    os.environ["FAKE_TEST_KEY"] = "DatabaseStorage"
    os.environ["BOBSLED_DATABASE_URI"] = "test://"
    Cls, args = get_env_config("FAKE_TEST_KEY", None, storages)
    assert Cls is storages.DatabaseStorage
    assert args == {"BOBSLED_DATABASE_URI": "test://"}

import os
from ..auth import YamlAuthStorage

ENV_FILE = os.path.join(os.path.dirname(__file__), "users.yml")


def test_check_login_success():
    auth = YamlAuthStorage(ENV_FILE)
    u = auth.check_login("sample", "password")
    assert u.username == "sample"


def test_check_login_fail():
    auth = YamlAuthStorage(ENV_FILE)
    assert auth.check_login("sample", "bad") is None
    assert auth.check_login("other", "none") is None

from starlette.testclient import TestClient
from ..web import app, bobsled
from ..utils import hash_password


def test_manage_users_permissions():
    # empty database, view should be accessible
    with TestClient(app) as client:
        resp = client.get("/manage_users")
        assert resp.status_code == 200

        # user in database, page redirects
        bobsled.storage.users["sample"] = hash_password("password")
        resp = client.get("/manage_users")
        assert resp.url == "http://testserver/login"
        assert resp.status_code == 200

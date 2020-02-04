from starlette.testclient import TestClient
from ..web import app, bobsled
from ..utils import hash_password


def setup():
    # reset in-memory users on each test
    bobsled.storage.users = {}


def test_not_logged_in():
    with TestClient(app) as client:
        response = client.get("/api/index")
    assert response.url == "http://testserver/login"


def test_manage_users_permissions():
    # empty database, view should be accessible
    with TestClient(app) as client:
        resp = client.get("/manage_users")
        assert resp.url == "http://testserver/manage_users"
        assert resp.status_code == 200

        # user in database, page redirects
        bobsled.storage.users["sample"] = (hash_password("password"), [])
        resp = client.get("/manage_users")
        assert resp.url == "http://testserver/login"
        assert resp.status_code == 200

        # logged in, not admin, page still redirects
        client.post("/login", {"username": "sample", "password": "password"})
        resp = client.get("/manage_users")
        assert resp.url == "http://testserver/login"
        assert resp.status_code == 200

        # logged in, as admin, page works again
        bobsled.storage.users["sample"] = (hash_password("password"), ["admin"])
        client.post("/login", {"username": "sample", "password": "password"})
        resp = client.get("/manage_users")
        assert resp.url == "http://testserver/manage_users"
        assert resp.status_code == 200
        assert resp.context["usernames"] == ["sample"]


def test_manage_users_add_errors():
    with TestClient(app) as client:
        # required fields
        resp = client.post("/manage_users")
        assert resp.status_code == 200
        assert "Username is required." in resp.context["errors"]
        assert "Password is required." in resp.context["errors"]

        # required fields
        resp = client.post(
            "/manage_users", {"password": "abc", "confirm_password": "xyz"}
        )
        assert "Username is required." in resp.context["errors"]
        assert "Passwords do not match." in resp.context["errors"]

        # already taken
        bobsled.storage.users["sample"] = (hash_password("password"), ["admin"])
        resp = client.post(
            "/manage_users",
            {"username": "sample", "password": "abc", "confirm_password": "abc"},
        )
        assert resp.is_redirect

        # oh right, we have to log in :)
        client.post("/login", {"username": "sample", "password": "password"})
        resp = client.post(
            "/manage_users",
            {"username": "sample", "password": "abc", "confirm_password": "abc"},
        )
        assert "Username is already taken." in resp.context["errors"]


def test_manage_users_good():
    with TestClient(app) as client:
        resp = client.post(
            "/manage_users",
            {
                "username": "sample",
                "password": "password",
                "confirm_password": "password",
                "permissions": "admin",
            },
        )
        assert not resp.is_redirect
        assert resp.status_code == 200
        assert not resp.context["errors"]
        assert "sample" in resp.context["usernames"]

        # to add a second user we need to login
        client.post("/login", {"username": "sample", "password": "password"})
        resp = client.post(
            "/manage_users",
            {"username": "number2", "password": "abc", "confirm_password": "abc"},
        )
        assert resp.status_code == 200
        assert not resp.context["errors"]
        assert len(resp.context["usernames"]) == 2

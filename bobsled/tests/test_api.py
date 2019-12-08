from starlette.testclient import TestClient

from ..web import app, bobsled
from ..base import User
from ..utils import hash_password


def setup():
    # have to get a working check_login, hack for MemoryStorage
    bobsled.storage.users["sample"] = User("sample", hash_password("password"))


# def test_not_logged_in():
#     with TestClient(app) as client:
#         response = client.get("/api/index")
#     assert response.status_code == 403


def test_index():
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/index")
    assert len(response.json()["tasks"]) == 3
    assert len(response.json()["runs"]) == 0


def test_overview():
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/task/hello-world")
    assert response.json()["task"]["image"] == "hello-world"
    assert len(response.json()["runs"]) == 0


def test_run_and_detail():
    # test these together because there's weirdness in running twice
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/task/hello-world/run")
        uuid = response.json()["uuid"]
        detail = client.get(f"/api/run/{uuid}")
    assert detail.json()["uuid"] == uuid


def test_websocket():
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/task/full-example/run")
    uuid = response.json()["uuid"]
    with client.websocket_connect(f"/ws/logs/{uuid}") as websocket:
        data = websocket.receive_json()
        assert data["logs"] == "**ONE/WORD** alpine\n"

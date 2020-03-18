from starlette.testclient import TestClient
from ..web import app, bobsled
from ..utils import hash_password
from ..base import User


def setup():
    # have to get a working check_login, hack for MemoryStorage
    bobsled.storage.users["sample"] = User("sample", hash_password("password"), [])
    bobsled.storage.users["admin"] = User("admin", hash_password("password"), ["admin"])


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


def test_run_perms():
    # test these together because there's weirdness in running twice
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/task/hello-world/run")
        assert response.json()["error"] == "Insufficient permissions."


def test_run_and_detail():
    # test these together because there's weirdness in running twice
    with TestClient(app) as client:
        client.post("/login", {"username": "admin", "password": "password"})
        response = client.get("/api/task/hello-world/run")
        uuid = response.json()["uuid"]
        detail = client.get(f"/api/run/{uuid}")
    assert detail.json()["uuid"] == uuid


def test_websocket():
    with TestClient(app) as client:
        client.post("/login", {"username": "admin", "password": "password"})
        response = client.get("/api/task/full-example/run")
    uuid = response.json()["uuid"]
    with client.websocket_connect(f"/ws/logs/{uuid}") as websocket:
        data = websocket.receive_json()
        assert data["logs"] == "'hello alpine'\n"


def test_update_tasks():
    with TestClient(app) as client:
        client.post("/login", {"username": "admin", "password": "password"})

        assert {"hello-world", "full-example", "forever"} == set(
            bobsled.storage.tasks.keys()
        )

        # change yaml file so that update_tasks has to do work
        bobsled.tasks.filename = "bobsled/tests/tasks/tasks2.yml"

        resp = client.post("/api/update_tasks")
        assert resp.status_code == 200
        assert {"hello-world2"} == {t["name"] for t in resp.json()["tasks"]}

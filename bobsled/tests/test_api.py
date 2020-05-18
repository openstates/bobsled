from starlette.testclient import TestClient
from ..web import app, bobsled
from ..utils import hash_password
from ..base import User, Run, Status


def setup():
    # have to get a working check_login, hack for MemoryStorage
    bobsled.storage.users["sample"] = User("sample", hash_password("password"), [])
    bobsled.storage.users["admin"] = User("admin", hash_password("password"), ["admin"])
    bobsled.storage.runs = []


def test_index():
    bobsled.storage.runs = [
        Run(
            "hello-world",
            Status.Success,
            "2020-01-01T00:00:00.0",
            "2020-01-01T01:00:00.0",
        ),
        Run(
            "hello-world",
            Status.Error,
            "2020-01-02T00:00:00.0",
            "2020-01-02T01:00:00.0",
        ),
        Run(
            "hello-world",
            Status.Success,
            "2020-01-03T00:00:00.0",
            "2020-01-04T01:00:00.0",
        ),
        Run("hello-world", Status.Running, "2020-01-04T00:00:00.0",),
    ]

    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/index")
    tasks = response.json()["tasks"]
    running = response.json()["runs"]
    assert len(tasks) == 3
    assert len(running) == 1

    hello = [t for t in tasks if t["name"] == "hello-world"][0]
    assert hello["latest_run"]["status"] == "Running"
    assert hello["recent_statuses"] == ["Running", "Success", "Error", "Success"]


def test_overview():
    bobsled.storage.runs = [
        Run(
            "hello-world",
            Status.Success,
            "2020-01-03T00:00:00.0",
            "2020-01-04T01:02:03.0",
        ),
    ]
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.get("/api/task/hello-world")
    assert response.json()["task"]["image"] == "hello-world"
    assert len(response.json()["runs"]) == 1
    assert response.json()["runs"][0]["duration"] == "25:02:03"


def test_run_perms():
    # test these together because there's weirdness in running twice
    with TestClient(app) as client:
        client.post("/login", {"username": "sample", "password": "password"})
        response = client.post("/api/task/hello-world/run")
        assert response.json()["error"] == "Insufficient permissions."


def test_run_and_detail():
    # test these together because there's weirdness in running twice
    with TestClient(app) as client:
        client.post("/login", {"username": "admin", "password": "password"})
        response = client.post("/api/task/hello-world/run")
        uuid = response.json()["uuid"]
        detail = client.get(f"/api/run/{uuid}")
    assert detail.json()["uuid"] == uuid


def test_websocket():
    with TestClient(app) as client:
        client.post("/login", {"username": "admin", "password": "password"})
        response = client.post("/api/task/full-example/run")
    uuid = response.json()["uuid"]
    with client.websocket_connect(f"/ws/logs/{uuid}") as websocket:
        data = websocket.receive_json()
        assert data["logs"] == "'**ONE/WORD** alpine'\n"


def test_update_tasks():
    with TestClient(app) as client:
        client.post("/login", {"username": "admin", "password": "password"})

        assert {"hello-world", "full-example", "forever"} == set(
            bobsled.storage.tasks.keys()
        )

        # change yaml file so that update_tasks has to do work
        bobsled.tasks.filename = "bobsled/tests/tasks/tasks2.yml"

        resp = client.post("/api/update_config")
        assert resp.status_code == 200
        assert {"hello-world2"} == {t["name"] for t in resp.json()["tasks"]}

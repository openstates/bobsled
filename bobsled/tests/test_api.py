from starlette.testclient import TestClient

from ..web import app


def test_index():
    client = TestClient(app)
    client.post("/login", {"username": "sample", "password": "password"})
    response = client.get("/api/index")
    assert len(response.json()["tasks"]) == 3
    assert len(response.json()["runs"]) == 0


def test_overview():
    client = TestClient(app)
    client.post("/login", {"username": "sample", "password": "password"})
    response = client.get("/api/task/hello-world")
    assert response.json()["task"]["image"] == "hello-world"
    assert len(response.json()["runs"]) == 0


def test_run_and_detail():
    # test these together because there's weirdness in running twice
    client = TestClient(app)
    client.post("/login", {"username": "sample", "password": "password"})
    response = client.get("/api/task/hello-world/run")
    uuid = response.json()["uuid"]
    detail = client.get(f"/api/run/{uuid}")
    assert detail.json()["uuid"] == uuid


def test_websocket():
    client = TestClient(app)
    client.post("/login", {"username": "sample", "password": "password"})
    response = client.get("/api/task/full-example/run")
    uuid = response.json()["uuid"]
    with client.websocket_connect(f"/ws/logs/{uuid}") as websocket:
        data = websocket.receive_json()
        assert data["logs"] == "**ONE/WORD** alpine\n"

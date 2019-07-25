from starlette.testclient import TestClient
import jwt

from ..web import app, bobsled


def test_login():
    client = TestClient(app)
    response = client.get('/api/login?username=sample&password=password')
    assert response.status_code == 200
    assert "token" in response.json()
    assert "username" in jwt.decode(response.json()["token"], bobsled.settings["secret_key"],
                                    algorithms=["HS256"])

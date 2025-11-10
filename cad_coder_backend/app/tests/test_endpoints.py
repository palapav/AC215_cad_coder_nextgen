from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_generate_cad():
    response = client.post("/generate_cad", data={"prompt": "draw a cube"})
    assert response.status_code == 200
    assert "cad_code" in response.json()

def test_health():
    assert client.get("/health/").json() == {"status": "ok"}

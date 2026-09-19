from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_sources():
    assert client.get("/api/sources").json() == ["autoru", "avito", "drom"]

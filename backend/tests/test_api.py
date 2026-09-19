from fastapi.testclient import TestClient
from app.main import app
from app.domain.catalog import CatalogResponse, CatalogNode
from app.api import routes

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_sources():
    assert client.get("/api/sources").json() == ["autoru", "avito", "drom"]

def test_autoru_catalog_endpoint(monkeypatch):
    def fake_fetch(**kwargs):
        return CatalogResponse(source="autoru", state=kwargs["state"], nodes=[CatalogNode(id="BMW", name="BMW", level="mark", offers_count=12)], total=1)
    monkeypatch.setattr(routes.autoru_catalog, "fetch", fake_fetch)
    response = client.get("/api/catalog/autoru?bc_lookup=BMW&state=USED")
    assert response.status_code == 200
    assert response.json()["nodes"][0]["id"] == "BMW"
    assert response.json()["nodes"][0]["offers_count"] == 12

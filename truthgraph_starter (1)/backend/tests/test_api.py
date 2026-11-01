from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_shape():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "model_loaded" in data
    assert data["service"] == "truthgraph-api"

def test_verify_rejects_short_claim():
    response = client.post("/api/verify", json={"claim": "abc"})
    assert response.status_code == 422

def test_verify_rejects_extra_fields():
    response = client.post("/api/verify", json={"claim": "A sufficiently long claim", "label": "Supported"})
    assert response.status_code == 422

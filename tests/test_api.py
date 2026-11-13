from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "train_cases" in data
    assert "test_cases" in data
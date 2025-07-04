"""
Tests for health endpoint
"""

from fastapi.testclient import TestClient
from poshub.api.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint returns 200 and correct response"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

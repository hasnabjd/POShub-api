import pytest
from fastapi.testclient import TestClient
from poshub_api.main import app

client = TestClient(app)

def test_health_check_with_correlation_id():
    """Test that health check endpoint works and includes correlation ID in response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "poshub-api"}
    assert "X-Correlation-ID" in response.headers

def test_correlation_id_preserved():
    """Test that custom correlation ID is preserved in response."""
    custom_correlation_id = "test-corr-123"
    response = client.get("/health", headers={"X-Correlation-ID": custom_correlation_id})
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_correlation_id

def test_correlation_id_generated():
    """Test that correlation ID is generated when not provided."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    # Should be a UUID format
    import uuid
    try:
        uuid.UUID(response.headers["X-Correlation-ID"])
    except ValueError:
        pytest.fail("Generated correlation ID is not a valid UUID")

def test_mockbin_endpoint_with_correlation_id():
    """Test that mockbin endpoint works with correlation ID."""
    custom_correlation_id = "mockbin-test-456"
    response = client.get("/mockbin", headers={"X-Correlation-ID": custom_correlation_id})
    # This might fail due to external API, but correlation ID should be preserved
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == custom_correlation_id 
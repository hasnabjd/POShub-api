from fastapi.testclient import TestClient

from poshub_api.main import app

client = TestClient(app)


def test_login_success():
    """Test successful login with admin user."""
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "orders:read" in data["scopes"]
    assert "orders:write" in data["scopes"]


def test_login_failure():
    """Test login failure with wrong credentials."""
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_json_success():
    """Test successful login with JSON endpoint."""
    response = client.post(
        "/auth/login-json", json={"username": "user", "password": "user123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "orders:read" in data["scopes"]
    assert (
        "orders:write" not in data["scopes"]
    )  # user doesn't have write access


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token."""
    response = client.get("/orders/123")
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token():
    """Test accessing protected endpoint with valid token."""
    # First login to get token
    login_response = client.post(
        "/auth/login", data={"username": "admin", "password": "admin123"}
    )
    token = login_response.json()["access_token"]

    # Use token to access protected endpoint
    response = client.get(
        "/orders/123", headers={"Authorization": f"Bearer {token}"}
    )
    # Should get 404 (order not found) but not 401 (unauthorized)
    assert response.status_code == 404


def test_scope_validation():
    """Test that scope validation works correctly."""
    # Login as user (only has orders:read)
    login_response = client.post(
        "/auth/login", data={"username": "user", "password": "user123"}
    )
    token = login_response.json()["access_token"]

    # Try to create order (requires orders:write)
    order_data = {
        "id": "test-order-123",
        "customer_name": "Test Customer",
        "items": [{"name": "Item 1", "price": 10.0}],
        "total": 10.0,
    }

    response = client.post(
        "/orders/",
        json=order_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403  # Forbidden - missing scope


def test_demo_endpoint_with_scope():
    """Test demo endpoint with proper scope."""
    # Login as demo user
    login_response = client.post(
        "/auth/login", data={"username": "demo", "password": "demo123"}
    )
    token = login_response.json()["access_token"]

    # Access demo endpoint
    response = client.get(
        "/demo/mockbin", headers={"Authorization": f"Bearer {token}"}
    )
    # Might fail due to external API, but should not be 401/403
    assert response.status_code not in [401, 403]


def test_user_profile():
    """Test getting current user profile."""
    # Login to get token
    login_response = client.post(
        "/auth/login", data={"username": "admin", "password": "admin123"}
    )
    token = login_response.json()["access_token"]

    # Get user profile
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert "orders:read" in data["scopes"]


def test_available_scopes():
    """Test getting available scopes."""
    response = client.get("/auth/scopes")
    assert response.status_code == 200
    data = response.json()
    assert "scopes" in data
    assert "orders:read" in data["scopes"]
    assert "orders:write" in data["scopes"]
    assert "demo:read" in data["scopes"]


def test_correlation_id_with_auth():
    """Test that correlation ID works with authentication."""
    # Login to get token
    login_response = client.post(
        "/auth/login", data={"username": "admin", "password": "admin123"}
    )
    token = login_response.json()["access_token"]

    # Make authenticated request with correlation ID
    custom_correlation_id = "auth-test-123"
    response = client.get(
        "/orders/123",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": custom_correlation_id,
        },
    )

    # Should preserve correlation ID
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == custom_correlation_id

import pytest
from fastapi.testclient import TestClient

from poshub_api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests pour l'endpoint de santé."""

    def test_health_check_200(self):
        """Test que l'endpoint health retourne 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "poshub-api"
        assert "X-Correlation-ID" in response.headers


class TestAuthentication:
    """Tests pour l'authentification."""

    def test_login_success_200(self):
        """Test login réussi retourne 200."""
        response = client.post(
            "/auth/login", data={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "orders:read" in data["scopes"]
        assert "orders:write" in data["scopes"]

    def test_login_failure_401(self):
        """Test login échoué retourne 401."""
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_json_success_200(self):
        """Test login JSON réussi retourne 200."""
        response = client.post(
            "/auth/login-json",
            json={"username": "user", "password": "user123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "orders:read" in data["scopes"]
        assert "orders:write" not in data["scopes"]

    def test_protected_endpoint_without_token_401(self):
        """Test endpoint protégé sans token retourne 401."""
        response = client.get("/orders/123")
        assert response.status_code == 401

    def test_user_profile_200(self):
        """Test récupération du profil utilisateur retourne 200."""
        # Login pour obtenir token
        login_response = client.post(
            "/auth/login", data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # Récupérer le profil
        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "orders:read" in data["scopes"]

    def test_available_scopes_200(self):
        """Test récupération des scopes disponibles retourne 200."""
        response = client.get("/auth/scopes")
        assert response.status_code == 200
        data = response.json()
        assert "scopes" in data
        assert "orders:read" in data["scopes"]
        assert "orders:write" in data["scopes"]
        assert "demo:read" in data["scopes"]


class TestOrdersEndpoints:
    """Tests pour les endpoints de commandes."""

    @pytest.fixture
    def admin_token(self):
        """Token d'administrateur pour les tests."""
        response = client.post(
            "/auth/login", data={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    @pytest.fixture
    def user_token(self):
        """Token d'utilisateur (lecture seule) pour les tests."""
        response = client.post(
            "/auth/login", data={"username": "user", "password": "user123"}
        )
        return response.json()["access_token"]

    def test_create_order_success_201(self, admin_token):
        """Test création de commande réussie retourne 201."""
        order_data = {
            "id": "test-order-001",
            "customer_name": "John Doe",
            "items": [
                {"name": "Pizza Margherita", "price": 12.50},
                {"name": "Coca Cola", "price": 2.50},
            ],
            "total": 15.00,
        }

        response = client.post(
            "/orders/",
            json=order_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-order-001"
        assert data["customer_name"] == "John Doe"
        assert len(data["items"]) == 2
        assert data["total"] == 15.00

    def test_create_order_unauthorized_401(self):
        """Test création de commande sans token retourne 401."""
        order_data = {
            "id": "test-order-002",
            "customer_name": "Jane Doe",
            "items": [],
            "total": 0.0,
        }

        response = client.post("/orders/", json=order_data)
        assert response.status_code == 401

    def test_create_order_forbidden_403(self, user_token):
        """Test création de commande avec scope insuffisant retourne 403."""
        order_data = {
            "id": "test-order-003",
            "customer_name": "Jane Doe",
            "items": [],
            "total": 0.0,
        }

        response = client.post(
            "/orders/",
            json=order_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_get_order_success_200(self, admin_token):
        """Test récupération de commande existante retourne 200."""
        # Créer d'abord une commande
        order_data = {
            "id": "test-order-004",
            "customer_name": "Alice Smith",
            "items": [{"name": "Burger", "price": 8.50}],
            "total": 8.50,
        }

        client.post(
            "/orders/",
            json=order_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Récupérer la commande
        response = client.get(
            "/orders/test-order-004",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-order-004"
        assert data["customer_name"] == "Alice Smith"

    def test_get_order_not_found_404(self, admin_token):
        """Test récupération de commande inexistante retourne 404."""
        response = client.get(
            "/orders/non-existent-order",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_order_unauthorized_401(self):
        """Test récupération de commande sans token retourne 401."""
        response = client.get("/orders/any-order")
        assert response.status_code == 401


class TestDemoEndpoints:
    """Tests pour les endpoints de démonstration."""

    @pytest.fixture
    def demo_token(self):
        """Token d'utilisateur demo pour les tests."""
        response = client.post(
            "/auth/login", data={"username": "demo", "password": "demo123"}
        )
        return response.json()["access_token"]

    def test_mockbin_success_200(self, demo_token):
        """Test endpoint mockbin avec token valide."""
        response = client.get(
            "/demo/mockbin", headers={"Authorization": f"Bearer {demo_token}"}
        )

        # Peut échouer à cause de l'API externe, mais ne doit pas être 401/403
        assert response.status_code not in [401, 403]

    def test_mockbin_unauthorized_401(self):
        """Test endpoint mockbin sans token retourne 401."""
        response = client.get("/demo/mockbin")
        assert response.status_code == 401

    def test_mockbin_forbidden_403(self):
        """Test endpoint mockbin avec scope insuffisant retourne 403."""
        # Utiliser un token sans le scope demo:read
        user_response = client.post(
            "/auth/login", data={"username": "user", "password": "user123"}
        )
        user_token = user_response.json()["access_token"]

        response = client.get(
            "/demo/mockbin", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestCorrelationID:
    """Tests pour la gestion des correlation IDs."""

    def test_correlation_id_preserved(self):
        """Test que le correlation ID est préservé dans la réponse."""
        custom_correlation_id = "test-corr-123"
        response = client.get(
            "/health", headers={"X-Correlation-ID": custom_correlation_id}
        )

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == custom_correlation_id

    def test_correlation_id_generated(self):
        """Test qu'un correlation ID est généré automatiquement."""
        response = client.get("/health")

        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers

        # Vérifier que c'est un UUID valide
        import uuid

        try:
            uuid.UUID(response.headers["X-Correlation-ID"])
        except ValueError:
            pytest.fail("Generated correlation ID is not a valid UUID")

    def test_correlation_id_with_auth(self):
        """Test que le correlation ID fonctionne avec l'authentification."""
        # Login pour obtenir token
        login_response = client.post(
            "/auth/login", data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # Requête authentifiée avec correlation ID
        custom_correlation_id = "auth-corr-456"
        response = client.get(
            "/orders/123",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Correlation-ID": custom_correlation_id,
            },
        )

        # Doit préserver le correlation ID même si la requête échoue (404)
        assert "X-Correlation-ID" in response.headers
        assert response.status_code == 404
        assert response.headers["X-Correlation-ID"] == custom_correlation_id


class TestErrorHandling:
    """Tests pour la gestion des erreurs."""

    def test_invalid_json_422(self):
        """Test requête avec JSON invalide retourne 422."""
        response = client.post(
            "/orders/",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_method_not_allowed_405(self):
        """Test méthode HTTP non autorisée retourne 405."""
        response = client.put("/health")
        assert response.status_code == 405

    def test_not_found_404(self):
        """Test endpoint inexistant retourne 404."""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404

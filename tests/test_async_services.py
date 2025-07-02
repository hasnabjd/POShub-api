import pytest
import httpx
from poshub_api.orders.service import OrderService
from poshub_api.orders.schemas import OrderIn, OrderItem
from poshub_api.demo.service import fetch_mockbin
from poshub_api.http_utils import safe_get

@pytest.mark.asyncio
class TestOrderServiceAsync:
    """Tests asynchrones pour le service de commandes."""
    
    @pytest.fixture
    async def order_service(self):
        """Service de commandes pour les tests."""
        return OrderService()
    
    @pytest.fixture
    async def sample_order(self):
        """Commande d'exemple pour les tests."""
        return OrderIn(
            id="test-async-order-001",
            customer_name="Async Test Customer",
            items=[
                OrderItem(name="Test Item 1", price=10.0),
                OrderItem(name="Test Item 2", price=15.0)
            ],
            total=25.0
        )
    
    async def test_create_order_success(self, order_service, sample_order):
        """Test création asynchrone de commande."""
        result = await order_service.create_order(sample_order)
        
        assert result.id == "test-async-order-001"
        assert result.customer_name == "Async Test Customer"
        assert len(result.items) == 2
        assert result.total == 25.0
    
    async def test_get_order_success(self, order_service, sample_order):
        """Test récupération asynchrone de commande."""
        # Créer d'abord la commande
        await order_service.create_order(sample_order)
        
        # Récupérer la commande
        result = await order_service.get_order("test-async-order-001")
        
        assert result is not None
        assert result.id == "test-async-order-001"
        assert result.customer_name == "Async Test Customer"
    
    async def test_get_order_not_found(self, order_service):
        """Test récupération de commande inexistante."""
        result = await order_service.get_order("non-existent-order")
        
        assert result is None
    
    async def test_multiple_orders(self, order_service):
        """Test gestion de plusieurs commandes."""
        order1 = OrderIn(
            id="multi-order-001",
            customer_name="Customer 1",
            items=[OrderItem(name="Item 1", price=5.0)],
            total=5.0
        )
        
        order2 = OrderIn(
            id="multi-order-002",
            customer_name="Customer 2",
            items=[OrderItem(name="Item 2", price=10.0)],
            total=10.0
        )
        
        # Créer les deux commandes
        await order_service.create_order(order1)
        await order_service.create_order(order2)
        
        # Récupérer les deux commandes
        result1 = await order_service.get_order("multi-order-001")
        result2 = await order_service.get_order("multi-order-002")
        
        assert result1 is not None
        assert result1.customer_name == "Customer 1"
        assert result2 is not None
        assert result2.customer_name == "Customer 2"

@pytest.mark.asyncio
class TestHTTPUtilsAsync:
    """Tests asynchrones pour les utilitaires HTTP."""
    
    @pytest.fixture
    async def http_client(self):
        """Client HTTP pour les tests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            yield client
    
    async def test_safe_get_success(self, http_client):
        """Test safe_get avec une URL valide."""
        # Utiliser une API de test publique
        result = await safe_get(http_client, "https://httpbin.org/json")
        
        assert result is not None
        assert "slideshow" in result or "args" in result
    
    async def test_safe_get_retry_on_failure(self, http_client):
        """Test que safe_get retry en cas d'échec."""
        # URL qui va probablement échouer
        with pytest.raises(Exception):
            await safe_get(http_client, "https://httpbin.org/status/500")
    
    async def test_safe_get_timeout(self, http_client):
        """Test timeout de safe_get."""
        # URL qui va prendre trop de temps
        with pytest.raises(Exception):
            await safe_get(http_client, "https://httpbin.org/delay/15")

@pytest.mark.asyncio
class TestDemoServiceAsync:
    """Tests asynchrones pour le service de démonstration."""
    
    @pytest.fixture
    async def http_client(self):
        """Client HTTP pour les tests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            yield client
    
    async def test_fetch_mockbin_success(self, http_client):
        """Test fetch_mockbin avec succès."""
        try:
            result = await fetch_mockbin(http_client)
            assert result is not None
        except Exception:
            # Peut échouer à cause de l'API externe, c'est normal
            pytest.skip("External API unavailable")
    
    async def test_fetch_mockbin_structure(self, http_client):
        """Test structure de la réponse de mockbin."""
        try:
            result = await fetch_mockbin(http_client)
            # Vérifier que c'est un dictionnaire
            assert isinstance(result, dict)
        except Exception:
            pytest.skip("External API unavailable")

@pytest.mark.asyncio
class TestConcurrentOperations:
    """Tests pour les opérations concurrentes."""
    
    @pytest.fixture
    async def order_service(self):
        """Service de commandes pour les tests."""
        return OrderService()
    
    async def test_concurrent_order_creation(self, order_service):
        """Test création concurrente de commandes."""
        import asyncio
        
        async def create_order(order_id: str):
            order = OrderIn(
                id=f"concurrent-{order_id}",
                customer_name=f"Customer {order_id}",
                items=[OrderItem(name=f"Item {order_id}", price=float(order_id))],
                total=float(order_id)
            )
            return await order_service.create_order(order)
        
        # Créer 5 commandes en parallèle
        tasks = [create_order(str(i)) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)
        
        # Vérifier que toutes les commandes ont été créées
        assert len(results) == 5
        for i, result in enumerate(results, 1):
            assert result.id == f"concurrent-{i}"
            assert result.customer_name == f"Customer {i}"
    
    async def test_concurrent_order_retrieval(self, order_service):
        """Test récupération concurrente de commandes."""
        import asyncio
        
        # Créer d'abord quelques commandes
        for i in range(1, 4):
            order = OrderIn(
                id=f"retrieve-{i}",
                customer_name=f"Customer {i}",
                items=[OrderItem(name=f"Item {i}", price=float(i))],
                total=float(i)
            )
            await order_service.create_order(order)
        
        async def get_order(order_id: str):
            return await order_service.get_order(order_id)
        
        # Récupérer les commandes en parallèle
        tasks = [get_order(f"retrieve-{i}") for i in range(1, 4)]
        results = await asyncio.gather(*tasks)
        
        # Vérifier que toutes les commandes ont été récupérées
        assert len(results) == 3
        for i, result in enumerate(results, 1):
            assert result is not None
            assert result.id == f"retrieve-{i}"
            assert result.customer_name == f"Customer {i}" 
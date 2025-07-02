# POSHub API

FastAPI-based POS system API with external service integration.

## Installation

```bash

# Add FastAPI and uvicorn dependencies
poetry add fastapi uvicorn

# Add additional dependencies for HTTP client, retry logic, and logging
poetry add httpx tenacity structlog

# Install all dependencies
poetry install
```

## Local Development

```bash
# Start the development server
poetry run uvicorn src.poshub_api.main:app --reload --host 0.0.0.0 --port 8000
```


## Testing

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/test_health.py

# Run only integration tests
poetry run pytest -m integration

# Run only async tests
poetry run pytest -m asyncio

# Run tests with verbose output
poetry run pytest -v

# Run tests and show coverage report
poetry run pytest --cov=src --cov-report=html
```

### Test Structure

- **`tests/test_api_integration.py`** - Tests d'intégration avec TestClient (sync)
- **`tests/test_async_services.py`** - Tests asynchrones avec pytest-asyncio
- **`tests/test_auth.py`** - Tests d'authentification JWT
- **`tests/test_correlation_id.py`** - Tests des correlation IDs

### Status Code Validation

Les tests vérifient les codes de statut HTTP :
- **200** - Succès (GET, PUT, PATCH)
- **201** - Création réussie (POST)
- **401** - Non authentifié
- **403** - Non autorisé (scope manquant)
- **404** - Ressource non trouvée
- **422** - Données invalides
- **405** - Méthode non autorisée

## Project Structure

```
src/poshub_api/
├── demo/              # Mock external service integration
├── orders/            # Order management
├── auth.py            # JWT authentication and scope validation
├── auth_router.py     # Authentication endpoints
├── http_client.py     # HTTP client injection
├── http_utils.py      # Safe HTTP utilities
├── logging_config.py  # Structured logging configuration
├── middleware.py      # Correlation ID middleware
└── main.py           # FastAPI application
```

## Features

- ✅ Async external API calls
- ✅ Single HTTP client with dependency injection
- ✅ Robust error handling with tenacity
- ✅ Structured logging with structlog
- ✅ Correlation ID tracking (X-Correlation-ID header)
- ✅ JWT authentication with HTTPBearer
- ✅ Scope-based authorization (orders:read, orders:write, demo:read)
- ✅ Health check endpoint
- ✅ Demo route for testing external services

## Correlation ID

The API automatically handles correlation IDs for request tracing:

- **Automatic generation**: If no `X-Correlation-ID` header is provided, a UUID is generated
- **Header preservation**: Custom correlation IDs are preserved and returned in response headers
- **Structured logging**: All log entries include the correlation ID for easy tracing
- **Request tracking**: Start/completion/error events are logged with correlation ID

Example usage:
```bash
# With custom correlation ID
curl -H "X-Correlation-ID: my-trace-123" http://localhost:8000/health

# Without correlation ID (auto-generated)
curl http://localhost:8000/health
```

## Authentication

The API uses JWT authentication with scope-based authorization:

### Login
```bash
# Get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Or with JSON
curl -X POST "http://localhost:8000/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Using JWT Token
```bash
# Access protected endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/orders/123

# Create order (requires orders:write scope)
curl -X POST "http://localhost:8000/orders/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "order-123", "customer_name": "John Doe", "items": [], "total": 0.0}'
```

### Test Users
- **admin** (admin123): Full access (orders:read, orders:write, demo:read)
- **user** (user123): Read-only access (orders:read)
- **demo** (demo123): Demo access only (demo:read)

## Docker

### Build et Run

```bash
# Build de l'image de production
docker build -t poshub-api .

# Run de l'image de production
docker run -p 8000:8000 poshub-api

# Build et run avec docker-compose (développement)
docker-compose up --build

# Run les tests avec docker-compose
docker-compose --profile test up --build

# Run le linting avec docker-compose
docker-compose --profile lint up --build
```

### Images Docker

- **Dockerfile** : Image de production optimisée (multi-stage build)
- **Dockerfile.dev** : Image de développement avec hot-reload
- **docker-compose.yml** : Orchestration pour développement et tests

## CI/CD

Le projet utilise GitHub Actions pour l'intégration continue :

### Workflow Automatisé

1. **Tests** : Exécution des tests unitaires et d'intégration
2. **Linting** : Vérification du style de code (flake8, black, isort)
3. **Security Scan** : Analyse de sécurité (bandit, safety)
4. **Build** : Construction de l'image Docker
5. **Deploy** : Déploiement automatique (staging/production)

### Déclencheurs

- **Push sur main** : Build + Deploy Production
- **Push sur develop** : Build + Deploy Staging
- **Pull Request** : Tests + Linting + Security

## Export OpenAPI

```bash
# Exporter la spécification OpenAPI en JSON
poetry run python scripts/export_openapi.py

# Ou directement avec curl
curl http://localhost:8000/openapi.json > openapi/poshub-api.json
```
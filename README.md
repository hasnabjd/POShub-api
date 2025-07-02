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
```

## Project Structure

```
src/poshub_api/
├── demo/          # Mock external service integration
├── orders/        # Order management
├── http_client.py # HTTP client injection
├── http_utils.py  # Safe HTTP utilities
└── main.py        # FastAPI application
```
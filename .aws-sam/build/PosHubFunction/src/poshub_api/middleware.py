import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger, set_correlation_id

logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to handle X-Correlation-ID header."""

    async def dispatch(self, request: Request, call_next):
        # Extract correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            correlation_id=correlation_id,
        )

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Log request completion
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                correlation_id=correlation_id,
            )

            return response

        except Exception as e:
            # Log request error
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                correlation_id=correlation_id,
            )
            raise

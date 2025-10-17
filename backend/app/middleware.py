"""
FastAPI middleware for request tracking and logging.
"""

import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request for log correlation.

    The request ID is:
    - Generated as a UUID for each request
    - Added to response headers as X-Request-ID
    - Bound to structlog context for automatic inclusion in all logs
    - Accessible via request.state.request_id
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for access in route handlers
        request.state.request_id = request_id

        # Bind to structlog context so all logs in this request include it
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            # Process request
            response = await call_next(request)

            # Add request ID to response headers for client correlation
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            # Clean up context
            structlog.contextvars.unbind_contextvars("request_id")

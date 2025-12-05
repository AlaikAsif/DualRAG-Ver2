"""Request/response logging middleware."""

from fastapi import Request
import logging
import time
from io import BytesIO

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    """Log all requests and responses."""
    start_time = time.time()
    
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

"""Middleware classes for LOOP web server."""

import time
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from utils.logger import get_logger

logger = get_logger("web")

class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers for static media files."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add cache headers for media files
        if request.url.path.startswith("/media/raw/"):
            # Cache media files for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["ETag"] = f'"{hash(request.url.path)}"'
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each HTTP request with method, path, status code, and processing time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f} ms)")
        return response

class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Handle concurrency limits gracefully and provide helpful error responses."""
    
    def __init__(self, app, max_concurrent: int = 3):
        super().__init__(app)
        self.max_concurrent = max_concurrent
        self.active_requests = 0
    
    async def dispatch(self, request: Request, call_next):
        # Skip concurrency check for static files and health checks
        if (request.url.path.startswith("/_next") or 
            request.url.path.startswith("/assets") or
            request.url.path.startswith("/media/raw") or
            request.url.path == "/"):
            return await call_next(request)
        
        if self.active_requests >= self.max_concurrent:
            logger.warning(f"Concurrency limit exceeded: {self.active_requests}/{self.max_concurrent} active requests")
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": f"Server busy. Too many concurrent requests ({self.active_requests}/{self.max_concurrent}). Please retry in a moment.",
                    "code": "CONCURRENCY_LIMIT_EXCEEDED",
                    "retry_after": 2  # Suggest retry after 2 seconds
                }
            )
        
        self.active_requests += 1
        try:
            response = await call_next(request)
            return response
        finally:
            self.active_requests -= 1

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Standardize error responses across the API."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled error in {request.method} {request.url.path}: {exc}", exc_info=True)
            
            # Map common exceptions to appropriate HTTP status codes
            if isinstance(exc, ValueError):
                status_code = 400
                message = str(exc)
            elif isinstance(exc, KeyError):
                status_code = 404
                message = f"Resource not found: {exc}"
            elif isinstance(exc, PermissionError):
                status_code = 403
                message = "Permission denied"
            elif isinstance(exc, FileNotFoundError):
                status_code = 404
                message = "File not found"
            else:
                status_code = 500
                message = "Internal server error"
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message": message,
                    "code": exc.__class__.__name__,
                    "timestamp": int(time.time())
                }
            ) 
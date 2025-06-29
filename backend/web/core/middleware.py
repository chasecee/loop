"""Middleware classes for LOOP web server."""

import time
import asyncio
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
        
        # Skip logging for static assets to reduce noise
        if (request.url.path.startswith("/_next") or 
            request.url.path.startswith("/assets") or
            request.url.path.startswith("/media/raw") or
            request.url.path.startswith("/media/processed") or
            request.url.path.endswith(('.js', '.css', '.woff', '.woff2', '.png', '.jpg', '.svg'))):
            return response
        
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f} ms)")
        return response

class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Handle concurrency limits gracefully and provide helpful error responses."""
    
    def __init__(self, app, max_concurrent: int = 3):
        super().__init__(app)
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def dispatch(self, request: Request, call_next):
        # Skip concurrency check for static files and health checks
        path = request.url.path
        if (path.startswith("/_next") or 
            path.startswith("/assets") or
            path.startswith("/media/") or
            path == "/" or
            path == "/favicon.ico" or
            path.endswith(('.js', '.css', '.woff', '.woff2', '.png', '.jpg', '.svg', '.ico', '.map'))):
            return await call_next(request)
        
        if self._semaphore.locked() and self._semaphore._value == 0:
            logger.warning("Concurrency limit exceeded – request rejected")
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "Server busy. Too many concurrent requests.",
                    "code": "CONCURRENCY_LIMIT_EXCEEDED",
                    "retry_after": 2,
                },
            )

        await self._semaphore.acquire()
        try:
            response = await call_next(request)
            return response
        finally:
            self._semaphore.release()

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


class ConditionalGZipMiddleware(BaseHTTPMiddleware):
    """
    GZip compression that only compresses responses, not file uploads.
    Skips compression for file upload requests to avoid memory issues.
    """
    
    def __init__(self, app, minimum_size: int = 1000):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Skip compression for file uploads
        if (request.method == "POST" and 
            request.url.path == "/api/media" and 
            request.headers.get("content-type", "").startswith("multipart/form-data")):
            logger.debug("Skipping gzip compression for file upload")
            return response
        
        # Skip compression for already compressed files or non-compressible content
        content_type = response.headers.get("content-type", "")
        if (content_type.startswith("image/") or 
            content_type.startswith("video/") or
            content_type.startswith("application/zip") or
            content_type.startswith("application/octet-stream")):
            return response
        
        # Only compress text-based responses (JSON, HTML, CSS, JS)
        if not (content_type.startswith("application/json") or
                content_type.startswith("text/") or
                content_type.startswith("application/javascript")):
            return response
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Skip compression if body is too small
        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # Compress the response
        import gzip
        compressed_body = gzip.compress(body)
        
        # Update headers
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed_body))
        
        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )

# ------------------------------------------------------------
# New: Upload progress tracking middleware
# ------------------------------------------------------------
# We stream reads from the ASGI receive channel so we can report
# granular progress for long multipart uploads (especially the
# /api/media endpoint). This eliminates the perceived "freeze"
# between the browser finishing its XHR upload and the backend
# starting processing.
#
# We purposefully implement this as a low-level ASGI middleware so we
# can wrap the original `receive` callable and observe each incoming
# body chunk before Starlette/FastAPI buffers the entire request.
# ------------------------------------------------------------


class UploadProgressMiddleware:
    """Track inbound HTTP request body size and broadcast progress.

    Currently enabled only for POST /api/media uploads with
    multipart/form-data bodies. Progress messages are sent to the
    existing WebSocket "progress" room with event type
    ``upload_progress``. Front-end clients can subscribe to that room
    to update UI state in real-time.
    """

    def __init__(self, app, chunk_threshold: int = 1 * 1024 * 1024):
        self.app = app
        # Broadcast every `chunk_threshold` bytes or on completion
        self.chunk_threshold = chunk_threshold

    async def __call__(self, scope, receive, send):
        # Only handle HTTP POSTs to /api/media with multipart bodies
        if (
            scope.get("type") == "http"
            and scope.get("method") == "POST"
            and scope.get("path") == "/api/media"
        ):
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            content_length = int(headers.get("content-length", 0)) or None

            bytes_seen = 0
            last_broadcast = 0

            async def receive_wrapper():
                nonlocal bytes_seen, last_broadcast
                message = await receive()

                if message["type"] == "http.request":
                    body_part = message.get("body", b"")
                    bytes_seen += len(body_part)

                    # Determine if we should broadcast (either threshold or completed)
                    if (
                        bytes_seen - last_broadcast >= self.chunk_threshold
                        or message.get("more_body") is False
                    ):
                        last_broadcast = bytes_seen

                        percent = None
                        if content_length:
                            # Avoid ZeroDivision, content_length > 0 here
                            percent = (bytes_seen / content_length) * 100.0

                        # Progress tracking - not needed in polling architecture
                        pass

                return message

            await self.app(scope, receive_wrapper, send)
        else:
            # Non-upload requests – passthrough unchanged
            await self.app(scope, receive, send) 
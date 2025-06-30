"""Middleware classes for LOOP web server."""

import time
import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError

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

# Upload progress tracking removed - polling architecture doesn't need it

class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request timing and basic info."""

    async def dispatch(self, request: Request, call_next):
        """Process request with timing."""
        start_time = time.time()
        
        # Skip timing for static files
        if request.url.path.startswith(("/_next", "/assets", "/media")):
            return await call_next(request)
        
        try:
            response = await call_next(request)
            
            # Calculate timing
            process_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log API requests only
            if request.url.path.startswith("/api/"):
                logger.info(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f} ms)")
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"{request.method} {request.url.path} - ERROR ({process_time:.2f} ms): {str(e)}")
            raise

class ResponseValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API responses match declared Pydantic models."""
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.validation_errors = []  # Track validation errors for debugging
        
    async def dispatch(self, request: Request, call_next):
        """Validate response against declared model."""
        response = await call_next(request)
        
        # Only validate API endpoints that return JSON
        if (not self.enabled or 
            not request.url.path.startswith("/api/") or
            not hasattr(response, 'body')):
            return response
        
        # Skip non-JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response
        
        try:
            # Parse response body
            if hasattr(response, 'body'):
                body = response.body.decode('utf-8') if response.body else "{}"
                response_data = json.loads(body)
                
                # Validate common response patterns
                validation_errors = self._validate_response_structure(
                    request.url.path, 
                    request.method, 
                    response_data
                )
                
                if validation_errors:
                    self.validation_errors.extend(validation_errors)
                    logger.warning(f"Response validation errors for {request.method} {request.url.path}: {validation_errors}")
                    
                    # In development, add validation errors to response headers
                    if logger.level <= 10:  # DEBUG level
                        response.headers["X-Validation-Errors"] = json.dumps(validation_errors)
                        
        except json.JSONDecodeError:
            # Skip validation for non-JSON responses
            pass
        except Exception as e:
            logger.error(f"Response validation failed for {request.url.path}: {e}")
        
        return response
    
    def _validate_response_structure(self, path: str, method: str, data: Any) -> List[str]:
        """Validate response structure against expected patterns."""
        errors = []
        
        # Most API endpoints should return APIResponse structure
        if path.startswith("/api/") and isinstance(data, dict):
            
            # Check APIResponse structure
            if "success" not in data:
                errors.append("Missing required 'success' field in APIResponse")
            elif not isinstance(data["success"], bool):
                errors.append("'success' field must be boolean")
                
            # Validate specific endpoint patterns
            if path == "/api/dashboard":
                errors.extend(self._validate_dashboard_response(data))
            elif path.startswith("/api/poll/"):
                errors.extend(self._validate_polling_response(data))
            elif path.startswith("/api/media"):
                errors.extend(self._validate_media_response(data))
                
        return errors
    
    def _validate_dashboard_response(self, data: Dict[str, Any]) -> List[str]:
        """Validate dashboard response structure."""
        errors = []
        
        if not data.get("success"):
            return errors  # Skip validation for error responses
            
        response_data = data.get("data", {})
        
        # Check required dashboard fields
        required_fields = ["status", "media", "loop", "active", "last_updated"]
        for field in required_fields:
            if field not in response_data:
                errors.append(f"Dashboard missing required field: {field}")
        
        # Validate status structure
        status = response_data.get("status", {})
        if isinstance(status, dict):
            if "timestamp" not in status:
                errors.append("Dashboard status missing timestamp")
            if "system" not in status:
                errors.append("Dashboard status missing system")
        
        # Validate media array
        media = response_data.get("media", [])
        if not isinstance(media, list):
            errors.append("Dashboard media must be array")
        
        return errors
    
    def _validate_polling_response(self, data: Dict[str, Any]) -> List[str]:
        """Validate polling endpoint responses."""
        errors = []
        
        if not data.get("success"):
            return errors
            
        response_data = data.get("data", {})
        
        # All polling responses should have timestamp
        if "timestamp" not in response_data:
            errors.append("Polling response missing timestamp")
        
        return errors
    
    def _validate_media_response(self, data: Dict[str, Any]) -> List[str]:
        """Validate media endpoint responses."""
        errors = []
        
        if not data.get("success"):
            return errors
            
        response_data = data.get("data", {})
        
        # Media list responses should have media array
        if "media" in response_data and not isinstance(response_data["media"], list):
            errors.append("Media response 'media' field must be array")
            
        return errors

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler middleware with better error messages."""

    async def dispatch(self, request: Request, call_next):
        """Handle errors globally."""
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise
        except ValidationError as e:
            # Better error messages for Pydantic validation errors
            logger.error(f"Validation error for {request.url.path}: {e}")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "message": "Validation error",
                    "errors": [{"field": error["loc"], "error": error["msg"]} for error in e.errors()]
                }
            )
        except Exception as e:
            # Catch all other exceptions
            logger.error(f"Unexpected error for {request.url.path}: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "error": str(e) if logger.level <= 10 else "An unexpected error occurred"
                }
            ) 
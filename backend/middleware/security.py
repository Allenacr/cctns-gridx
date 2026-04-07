"""
CCTNS-GridX — Security Middleware
Rate limiting, security headers, and request logging.
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

logger = logging.getLogger("cctns_gridx")

# Simple in-memory rate limiter
_rate_limit_store: dict = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 200    # requests per window


async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["X-Powered-By"] = "CCTNS-GridX"
    return response


async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    if client_ip in _rate_limit_store:
        window_start, count = _rate_limit_store[client_ip]
        if current_time - window_start < RATE_LIMIT_WINDOW:
            if count >= RATE_LIMIT_MAX:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                )
            _rate_limit_store[client_ip] = (window_start, count + 1)
        else:
            _rate_limit_store[client_ip] = (current_time, 1)
    else:
        _rate_limit_store[client_ip] = (current_time, 1)

    response = await call_next(request)
    return response


async def request_logger_middleware(request: Request, call_next):
    """Log all incoming requests."""
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration}ms)")
    return response

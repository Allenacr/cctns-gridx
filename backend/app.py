"""
CCTNS-GridX — FastAPI Application
Main application factory with all route registrations.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("cctns_gridx")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="CCTNS-GridX API",
        description="Crime Predictive Model & Hotspot Mapping Platform — Tamil Nadu Police",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # ─── CORS ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Security Middleware ───────────────────────────────
    from backend.middleware.security import (
        security_headers_middleware,
        rate_limit_middleware,
        request_logger_middleware,
    )
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(request_logger_middleware)

    # ─── Route Registration ────────────────────────────────
    from backend.routes.auth_routes import router as auth_router
    from backend.routes.fir_routes import router as fir_router
    from backend.routes.analytics_routes import router as analytics_router
    from backend.routes.map_routes import router as map_router
    from backend.routes.patrol_routes import router as patrol_router
    from backend.routes.women_safety_routes import router as safety_router

    app.include_router(auth_router)
    app.include_router(fir_router)
    app.include_router(analytics_router)
    app.include_router(map_router)
    app.include_router(patrol_router)
    app.include_router(safety_router)

    # ─── Static Files (Frontend) ───────────────────────────
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
        app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
        assets_dir = os.path.join(frontend_dir, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # ─── Serve Frontend Pages ──────────────────────────────
    @app.get("/", include_in_schema=False)
    async def serve_login():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    page_names = [
        "dashboard", "fir_entry", "hotspot_map", "analytics",
        "patrol", "women_safety", "behavioral", "accident_zones",
    ]
    for page in page_names:
        def _make_handler(p):
            async def handler():
                return FileResponse(os.path.join(frontend_dir, f"{p}.html"))
            return handler
        app.get(f"/{page}", include_in_schema=False)(_make_handler(page))

    # ─── Health Check ──────────────────────────────────────
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "CCTNS-GridX",
            "version": "1.0.0",
        }

    logger.info("CCTNS-GridX API initialized")
    return app

"""
Memora FastAPI Application Factory.
Sets up middleware, lifespan management, and routers.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memora.config import settings
from memora.memory.client import sibyl_manager
from memora.api.routes_incidents import router as incidents_router
from memora.api.routes_outcomes import router as outcomes_router
from memora.api.routes_memory import router as memory_router

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("memora.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure Sibyl connection is validated
    logger.info("Starting Memora Backend (Env: %s)...", settings.APP_ENV)
    try:
        client = sibyl_manager.get_client()
        logger.info("Connected to Sibyl Memory SQLite DB at: %s", sibyl_manager.db_path)
    except Exception as e:
        logger.error("WARNING: Failed to connect to Sibyl Memory at startup: %s", e)
    yield
    # Shutdown: close resources cleanly
    logger.info("Shutting down Memora Backend...")
    sibyl_manager.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="MEMORA API",
        description=(
            "AI operational memory agent for security operations teams. "
            "Built with load-bearing persistent Sibyl Memory."
        ),
        version="0.1.0",
        lifespan=lifespan
    )

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if not origins or settings.APP_ENV == "development":
        # Ensure local development hosts are always permitted
        origins = list(set(origins + [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ]))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(incidents_router)
    app.include_router(outcomes_router)
    app.include_router(memory_router)

    @app.get("/health", tags=["System"])
    def health_check():
        sibyl_ok = sibyl_manager.is_healthy()
        return {
            "status": "healthy" if sibyl_ok else "degraded",
            "sibyl_memory_connected": sibyl_ok,
            "version": "0.1.0"
        }

    return app


app = create_app()

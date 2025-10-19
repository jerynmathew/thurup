# backend/app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.api.v1.persistence_integration import restore_active_games
from app.core.game_server import init_game_server, shutdown_game_server
from app.db.cleanup import start_cleanup_task, stop_cleanup_task
from app.db.config import close_db, init_db
from app.logging_config import configure_logging, get_logger
from app.middleware import RequestIDMiddleware

# Configure structured logging
# Use JSON logs in production (when LOG_JSON=true), pretty console logs in development
json_logs = os.getenv("LOG_JSON", "false").lower() == "true"
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(json_logs=json_logs, log_level=log_level)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown tasks."""
    # Startup
    logger.info("application_starting")
    init_game_server()  # Initialize GameServer singleton
    await init_db()
    await restore_active_games()
    await start_cleanup_task()
    logger.info("application_ready")

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await stop_cleanup_task()
    await shutdown_game_server()  # Shutdown GameServer (cancel bot tasks)
    await close_db()
    logger.info("application_shutdown_complete")


app = FastAPI(title="Thurup Backend (FastAPI)", lifespan=lifespan)

# CORS Configuration from environment
# IMPORTANT: CORS middleware must be added BEFORE including routers
cors_origins_str = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
logger.info("cors_configuration", origins=origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware (after CORS)
app.add_middleware(RequestIDMiddleware)

# Include API router
app.include_router(api_router)

# Log startup
logger.info("application_startup", json_logs=json_logs, log_level=log_level)


@app.get("/")
async def root():
    return {"msg": "Thurup backend running. Use /docs for API."}

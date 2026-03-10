"""Chart-Monitor FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.storage.poller import start_poller, stop_poller

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)

# Resolve absolute path to the frontend directory regardless of CWD.
# Layout: backend/src/main.py  →  ../../frontend/src
_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup / shutdown lifecycle."""
    logger.info("Chart-Monitor starting up …")
    await start_poller()
    yield
    logger.info("Chart-Monitor shutting down …")
    await stop_poller()


app = FastAPI(
    title="Chart-Monitor",
    description="Dynamic data extraction, transformation, and dashboard visualization engine.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# API endpoints (must be included BEFORE the static mount so /api/* routes win)
app.include_router(router, prefix="/api/v1")

# Serve the Vanilla frontend at root.  html=True makes '/' serve index.html.
if _FRONTEND_DIR.exists():
    logger.info("Serving frontend from %s", _FRONTEND_DIR)
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="static")
else:
    logger.warning(
        "Frontend directory not found at %s – running in API-only mode.", _FRONTEND_DIR
    )

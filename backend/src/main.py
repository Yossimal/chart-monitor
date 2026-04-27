"""Chart-Monitor FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.storage.poller import start_poller, stop_poller

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)

# Resolve absolute paths relative to this file.
# Layout: backend/src/main.py  →  ../../frontend/src
#                               →  ../../docs/site  (MkDocs build output)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FRONTEND_DIR = _REPO_ROOT / "frontend" / "src"
_DOCS_DIR = _REPO_ROOT / "docs" / "site"


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
    version="0.2.0",
    lifespan=lifespan,
    # Swagger/OpenAPI moved to /api/docs so /docs is free for MkDocs
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# API endpoints (must be included BEFORE the static mount so /api/* routes win)
app.include_router(router, prefix="/api/v1")

# /docs → /docs/ redirect: Starlette's StaticFiles directory-index redirect
# produces "/" instead of "/docs/" when mounted at "/docs", so we handle it explicitly.
@app.get("/docs", include_in_schema=False)
async def docs_root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/docs/")

# Serve MkDocs built docs at /docs/ (must be mounted BEFORE the / catch-all)
if _DOCS_DIR.exists():
    logger.info("Serving docs from %s", _DOCS_DIR)
    app.mount("/docs", StaticFiles(directory=str(_DOCS_DIR), html=True), name="docs")
else:
    logger.warning(
        "Docs directory not found at %s – run: cd docs && python -m mkdocs build", _DOCS_DIR
    )

# Serve the Vanilla frontend at root.  html=True makes '/' serve index.html.
if _FRONTEND_DIR.exists():
    logger.info("Serving frontend from %s", _FRONTEND_DIR)
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="static")
else:
    logger.warning(
        "Frontend directory not found at %s – running in API-only mode.", _FRONTEND_DIR
    )

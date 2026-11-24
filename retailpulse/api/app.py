"""
FastAPI Application Entry Point for RetailPulse BI Agent.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from retailpulse.config import settings, DB_PATH
from retailpulse.core.logger import get_logger
from retailpulse.api.routes import router as api_router
from retailpulse.data.ingestion import run_ingestion_pipeline

logger = get_logger("retailpulse.app")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook: ensures clean database and data on application startup."""
    logger.info("Initializing RetailPulse AI System...")
    if not DB_PATH.exists():
        logger.info("Database file not found on startup. Executing initial ingestion pipeline...")
        run_ingestion_pipeline(force_regenerate=True)
    else:
        logger.info(f"Database online at {DB_PATH}.")
    yield
    logger.info("Shutting down RetailPulse AI System...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Data Analyst & Business Intelligence Agent for E-Commerce Data",
    lifespan=lifespan
)

# Enable CORS for local development and integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)

# Mount static files for dashboard frontend
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"])
async def serve_dashboard():
    """Serves the interactive BI dashboard and AI analyst chat interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>RetailPulse AI Dashboard initializing...</h1>")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the request.", "error": str(exc)}
    )

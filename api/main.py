"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import gc
import logging

from .config import API_TITLE, API_VERSION, API_DESCRIPTION
from .routes import router
from .database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["API v1"])


@app.middleware("http")
async def free_memory_after_request(request: Request, call_next):
    """Run GC after each request to promptly release query result memory."""
    response = await call_next(request)
    # Collect all generations explicitly so short-lived result objects from
    # DuckDB queries are freed before the next request arrives.
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting Wikipedia DuckDB API...")
    try:
        # Test database connection
        db_manager.get_connection()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API...")
    db_manager.close()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""FastAPI main application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from backend.config import API_HOST, API_PORT
from backend.api.routes import metrics, drivers, constructors
from backend.api.schemas import HealthCheck
from backend.data.cache import metric_cache


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("F1 Metrics API starting up...")

    # Test data loading
    try:
        from backend.data.loader import data_loader
        drivers = data_loader.get_drivers()
        logger.info(f"Successfully loaded {len(drivers)} drivers")

        races = data_loader.get_races()
        logger.info(f"Successfully loaded {len(races)} races")

    except Exception as e:
        logger.error(f"Failed to load initial data: {e}")
        raise

    yield

    # Shutdown
    logger.info("F1 Metrics API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="F1 Performance Metrics API",
    description="Comprehensive F1 driver and constructor performance metrics system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
import os

# Configure CORS origins based on environment
if os.getenv("ENVIRONMENT") == "production":
    # Production origins - Streamlit Community Cloud domains
    allowed_origins = [
        "https://*.streamlit.app",
        "https://*.streamlitapp.com",
        "http://localhost:8501"  # Keep localhost for testing
    ]
else:
    # Development - allow all origins
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(drivers.router, prefix="/api/v1")
app.include_router(constructors.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "F1 Performance Metrics API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/api/v1/metrics/available",
            "drivers": "/api/v1/drivers/",
            "constructors": "/api/v1/constructors/"
        }
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        # Test data access
        from backend.data.loader import data_loader
        drivers = data_loader.get_drivers()
        data_healthy = len(drivers) > 0

        # Get cache stats
        cache_stats = metric_cache.get_stats()

        return HealthCheck(
            status="healthy" if data_healthy else "unhealthy",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            cache_stats=cache_stats
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/v1/cache/clear")
async def clear_cache(metric_name: str = None):
    """Clear metric cache."""
    try:
        metric_cache.clear(metric_name)
        from backend.data.loader import data_loader
        data_loader.clear_cache()

        return {
            "message": f"Cache cleared for {metric_name or 'all metrics'}",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clearing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Also start Streamlit if available
    import subprocess
    import threading
    import time

    def start_streamlit():
        """Start Streamlit frontend."""
        time.sleep(2)  # Wait for FastAPI to start
        try:
            subprocess.run([
                "streamlit", "run", "frontend/app.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ])
        except Exception as e:
            logger.error(f"Failed to start Streamlit: {e}")

    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    streamlit_thread.start()

    logger.info("Starting FastAPI server...")
    logger.info(f"API will be available at: http://{API_HOST}:{API_PORT}")
    logger.info(f"API docs will be available at: http://{API_HOST}:{API_PORT}/docs")
    logger.info("Streamlit frontend will be available at: http://localhost:8501")

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
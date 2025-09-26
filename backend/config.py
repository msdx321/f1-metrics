"""Configuration settings for F1 metrics system."""

from pathlib import Path

# Data paths
DATASET_DIR = Path("dataset")
CACHE_DIR = Path("cache")

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Frontend settings
FRONTEND_PORT = 8501
API_BASE_URL = f"http://localhost:{API_PORT}/api/v1"

# Data filtering
MIN_YEAR = 2011  # Complete data availability from 2011

# Cache settings
ENABLE_CACHE = True
CACHE_TTL = 3600  # 1 hour in seconds
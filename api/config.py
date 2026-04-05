"""Configuration settings for the Wikipedia DuckDB API."""
from pathlib import Path
import os

# Database
DB_PATH = Path(os.getenv('DB_PATH', '/app/wiki_data.duckdb'))
TABLE_NAME = 'wiki_articles'

# API
API_TITLE = "Wikipedia DuckDB API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Fast search and access API for Wikipedia database"

# Query limits
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
DEFAULT_OFFSET = 0

# Cache settings
ENABLE_CACHE = True
CACHE_TTL = 172800  # 2 days  in seconds

# DuckDB memory limit (passed as a PRAGMA after connecting)
DUCKDB_MEMORY_LIMIT = os.getenv('DUCKDB_MEMORY_LIMIT', '1GB')

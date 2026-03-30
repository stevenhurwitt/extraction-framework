"""Configuration settings for the Wikipedia DuckDB API."""
from pathlib import Path

# Database
DB_PATH = Path('/home/steven/extraction-framework/wiki_data.duckdb')
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
CACHE_TTL = 3600  # 1 hour in seconds

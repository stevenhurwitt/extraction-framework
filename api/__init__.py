"""__init__.py for the API package."""

from .main import app
from .database import db_manager
from .models import Article, SearchResult, DatabaseStats, HealthResponse

__all__ = [
    "app",
    "db_manager",
    "Article",
    "SearchResult",
    "DatabaseStats",
    "HealthResponse"
]

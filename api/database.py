"""Database connection and query utilities."""
import duckdb
import time
from typing import List, Dict, Any, Optional
from functools import lru_cache
import logging

from .config import DB_PATH, TABLE_NAME, ENABLE_CACHE, CACHE_TTL, DUCKDB_MEMORY_LIMIT

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages DuckDB connections and queries."""

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize database manager.
        
        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = db_path
        self._connection = None
        self._stats_cache: Optional[Dict[str, Any]] = None
        self._stats_cache_time: float = 0.0

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection.
        
        Returns:
            DuckDB connection object
        """
        if self._connection is None:
            try:
                self._connection = duckdb.connect(self.db_path, read_only=True)
                self._connection.execute(f"SET memory_limit='{DUCKDB_MEMORY_LIMIT}'")
                logger.info(f"Connected to database: {self.db_path} (memory limit: {DUCKDB_MEMORY_LIMIT})")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def search_by_title(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        include_text: bool = False
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search articles by title.
        
        Args:
            query: Search term for title
            limit: Maximum results to return
            offset: Number of results to skip
            include_text: Whether to include full text
            
        Returns:
            Tuple of (articles list, total count)
        """
        con = self.get_connection()

        # Fetch count and paginated results in a single pass using a window function.
        cols = "title, LENGTH(text) as text_length" if not include_text else "title, text, LENGTH(text) as text_length"

        search_query = f"""
            SELECT {cols}, COUNT(*) OVER () as total_count
            FROM {TABLE_NAME}
            WHERE title ILIKE ?
            LIMIT ? OFFSET ?
        """

        results = con.execute(search_query, [f"%{query}%", limit, offset]).fetchall()

        if not results:
            return [], 0

        total = results[0][-1]
        articles = []
        for row in results:
            articles.append({
                'title': row[0],
                'text': row[1] if include_text else None,
                'text_length': row[1] if not include_text else row[2],
            })

        return articles, total

    def search_by_content(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Search articles by content.
        
        Args:
            query: Search term for content
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            Tuple of (articles list, total count)
        """
        con = self.get_connection()

        # Fetch count and paginated results in a single pass using a window function.
        search_query = f"""
            SELECT title, LENGTH(text) as text_length, COUNT(*) OVER () as total_count
            FROM {TABLE_NAME}
            WHERE text ILIKE ?
            LIMIT ? OFFSET ?
        """

        results = con.execute(search_query, [f"%{query}%", limit, offset]).fetchall()

        if not results:
            return [], 0

        total = results[0][2]
        articles = [{'title': row[0], 'text_length': row[1], 'text': None} for row in results]

        return articles, total

    def get_article_by_title(self, title: str, include_text: bool = True) -> Optional[Dict[str, Any]]:
        """Get a single article by title.
        
        Args:
            title: Article title
            include_text: Whether to include full text
            
        Returns:
            Article dict or None if not found
        """
        con = self.get_connection()
        
        cols = "title, LENGTH(text) as text_length" if not include_text else "title, text, LENGTH(text) as text_length"
        
        query = f"""
            SELECT {cols} FROM {TABLE_NAME}
            WHERE title = ?
            LIMIT 1
        """
        
        result = con.execute(query, [title]).fetchone()
        
        if result is None:
            return None
        
        if include_text:
            return {'title': result[0], 'text': result[1], 'text_length': result[2]}
        else:
            return {'title': result[0], 'text_length': result[1], 'text': None}

    def get_random_article(self, include_text: bool = False) -> Optional[Dict[str, Any]]:
        """Get a random article.
        
        Args:
            include_text: Whether to include full text
            
        Returns:
            Article dict or None if table is empty
        """
        con = self.get_connection()

        # Use USING SAMPLE for efficient random sampling instead of ORDER BY RANDOM()
        # which requires a full table sort.
        cols = "title, LENGTH(text) as text_length" if not include_text else "title, text, LENGTH(text) as text_length"
        
        query = f"""
            SELECT {cols} FROM {TABLE_NAME}
            USING SAMPLE 1
        """
        
        result = con.execute(query).fetchone()
        
        if result is None:
            return None
        
        if include_text:
            return {'title': result[0], 'text': result[1], 'text_length': result[2]}
        else:
            return {'title': result[0], 'text_length': result[1], 'text': None}

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database stats
        """
        if ENABLE_CACHE and self._stats_cache is not None:
            if time.monotonic() - self._stats_cache_time < CACHE_TTL:
                return self._stats_cache

        con = self.get_connection()

        # Compute text lengths once in a subquery so LENGTH(text) is only
        # evaluated once per row instead of four times.
        query = f"""
            SELECT
                COUNT(*) as total_articles,
                AVG(text_len) as avg_text_length,
                MAX(text_len) as max_text_length,
                MIN(text_len) as min_text_length
            FROM (
                SELECT LENGTH(text) AS text_len FROM {TABLE_NAME}
            )
        """
        
        result = con.execute(query).fetchone()
        
        stats = {
            'total_articles': int(result[0]),
            'avg_text_length': float(result[1]) if result[1] else 0,
            'max_text_length': int(result[2]) if result[2] else 0,
            'min_text_length': int(result[3]) if result[3] else 0
        }

        if ENABLE_CACHE:
            self._stats_cache = stats
            self._stats_cache_time = time.monotonic()

        return stats

    def is_connected(self) -> bool:
        """Check if database is accessible.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            con = self.get_connection()
            con.execute(f"SELECT 1 FROM {TABLE_NAME} LIMIT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

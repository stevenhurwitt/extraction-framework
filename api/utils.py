"""Utility functions for the API."""
from typing import List
from datetime import datetime, timedelta
import hashlib


def hash_query(query: str) -> str:
    """Generate a hash for a query string for caching.
    
    Args:
        query: Query string to hash
        
    Returns:
        SHA256 hash of the query
    """
    return hashlib.sha256(query.encode()).hexdigest()


def get_cache_key(endpoint: str, **params) -> str:
    """Generate a cache key from endpoint and parameters.
    
    Args:
        endpoint: API endpoint name
        **params: Query parameters
        
    Returns:
        Cache key string
    """
    param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{endpoint}:{param_str}"


def is_cache_expired(cached_time: datetime, ttl: int) -> bool:
    """Check if a cached item has expired.
    
    Args:
        cached_time: Time when item was cached
        ttl: Time to live in seconds
        
    Returns:
        True if cached item has expired
    """
    return datetime.now() > cached_time + timedelta(seconds=ttl)


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def format_query_string(query: str) -> str:
    """Clean and format a query string.
    
    Args:
        query: Raw query string
        
    Returns:
        Formatted query string
    """
    # Remove extra whitespace
    query = " ".join(query.split())
    # Strip leading/trailing whitespace
    query = query.strip()
    return query

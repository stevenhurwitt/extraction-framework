"""API routes and endpoints."""
from fastapi import APIRouter, Query, HTTPException, Path as FastAPIPath
from typing import Optional
import logging

from models import Article, SearchResult, DatabaseStats, HealthResponse
from database import db_manager
from config import DEFAULT_LIMIT, MAX_LIMIT, DEFAULT_OFFSET

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health."""
    db_connected = db_manager.is_connected()
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        database_connected=db_connected,
        message="API is running" if db_connected else "Database connection failed"
    )


@router.get("/statistics", response_model=DatabaseStats, tags=["Statistics"])
async def get_statistics():
    """Get database statistics."""
    try:
        stats = db_manager.get_statistics()
        return DatabaseStats(**stats)
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/articles/search", response_model=SearchResult, tags=["Search"])
async def search_articles(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    search_type: str = Query(
        "title",
        regex="^(title|content|both)$",
        description="Search in title, content, or both"
    ),
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Number of results (max {MAX_LIMIT})"
    ),
    offset: int = Query(
        DEFAULT_OFFSET,
        ge=0,
        description="Number of results to skip"
    ),
    include_text: bool = Query(
        False,
        description="Include full article text in results"
    )
):
    """Search articles by title or content.
    
    - **q**: Search query (required)
    - **search_type**: Search in 'title', 'content', or 'both' (default: title)
    - **limit**: Number of results to return (default: 20, max: 100)
    - **offset**: Number of results to skip (default: 0)
    - **include_text**: Include full text in results (default: false)
    """
    try:
        if search_type in ["title", "both"]:
            articles, total = db_manager.search_by_title(q, limit, offset, include_text)
            
            if search_type == "both":
                # Also search content and combine results
                content_articles, content_total = db_manager.search_by_content(q, limit, offset)
                # Deduplicate by title
                titles_seen = {a['title'] for a in articles}
                for article in content_articles:
                    if article['title'] not in titles_seen:
                        articles.append(article)
                        titles_seen.add(article['title'])
                total = len(titles_seen)
        else:
            articles, total = db_manager.search_by_content(q, limit, offset)
        
        return SearchResult(
            articles=[Article(**a) for a in articles],
            total_count=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/articles/{title}", response_model=Article, tags=["Articles"])
async def get_article(
    title: str = FastAPIPath(..., min_length=1, max_length=256, description="Article title"),
    include_text: bool = Query(True, description="Include full article text")
):
    """Get a single article by title."""
    try:
        article = db_manager.get_article_by_title(title, include_text)
        
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return Article(**article)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching article: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch article")


@router.get("/articles/random", response_model=Article, tags=["Articles"])
async def get_random_article(
    include_text: bool = Query(False, description="Include full article text")
):
    """Get a random article."""
    try:
        article = db_manager.get_random_article(include_text)
        
        if article is None:
            raise HTTPException(status_code=404, detail="No articles found in database")
        
        return Article(**article)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching random article: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch random article")

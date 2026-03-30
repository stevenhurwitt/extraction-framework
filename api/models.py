"""Pydantic models for API requests and responses."""
from typing import Optional, List
from pydantic import BaseModel, Field


class Article(BaseModel):
    """Single article data model."""
    title: str = Field(..., description="Article title")
    text_length: Optional[int] = Field(None, description="Length of article text in characters")
    text: Optional[str] = Field(None, description="Full article text")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Python",
                "text_length": 50000,
                "text": None
            }
        }


class SearchResult(BaseModel):
    """Search results wrapper."""
    articles: List[Article] = Field(..., description="List of matching articles")
    total_count: int = Field(..., description="Total number of matching articles")
    limit: int = Field(..., description="Limit applied to this query")
    offset: int = Field(..., description="Offset applied to this query")

    class Config:
        json_schema_extra = {
            "example": {
                "articles": [
                    {"title": "Python", "text_length": 50000, "text": None}
                ],
                "total_count": 42,
                "limit": 20,
                "offset": 0
            }
        }


class DatabaseStats(BaseModel):
    """Database statistics model."""
    total_articles: int = Field(..., description="Total number of articles")
    avg_text_length: float = Field(..., description="Average article text length")
    max_text_length: int = Field(..., description="Maximum article text length")
    min_text_length: int = Field(..., description="Minimum article text length")

    class Config:
        json_schema_extra = {
            "example": {
                "total_articles": 1000000,
                "avg_text_length": 3500.5,
                "max_text_length": 500000,
                "min_text_length": 100
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    database_connected: bool = Field(..., description="Whether database is accessible")
    message: Optional[str] = Field(None, description="Additional message")

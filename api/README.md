# Wikipedia DuckDB API

A fast, modern FastAPI for searching and accessing Wikipedia articles stored in a DuckDB database.

## Features

- 🚀 **FastAPI** - High-performance async API framework
- 🔍 **Full Search** - Search by title, content, or both
- 📊 **Statistics** - Get database stats (total articles, text length metrics)
- 🎲 **Random Articles** - Get random articles for browsing
- 📄 **Flexible Results** - Control result size and pagination
- 🏥 **Health Checks** - Monitor API and database status
- 📚 **Auto-Documentation** - Built-in Swagger UI and ReDoc

## Quick Start

### Installation

```bash
# Navigate to the api directory
cd /home/steven/extraction-framework/api

# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
# From the api directory
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

The API will be available at `http://192.168.0.9:8002`

- Interactive API docs: `http://192.168.0.9:8002/docs`
- Alternative API docs: `http://192.168.0.9:8002/redoc`

## API Endpoints

### Health & Stats

- `GET /api/v1/health` - Check API status
- `GET /api/v1/statistics` - Get database statistics

### Search

- `GET /api/v1/articles/search?q=<query>&search_type=title|content|both` - Search articles
  - Query parameters:
    - `q` (required): Search term
    - `search_type`: "title" (default), "content", or "both"
    - `limit`: Results per page (1-100, default: 20)
    - `offset`: Skip N results (default: 0)
    - `include_text`: Include full text (default: false)

### Single Article

- `GET /api/v1/articles/{title}` - Get article by title
  - Query parameters:
    - `include_text`: Include full text (default: true)

- `GET /api/v1/articles/random?include_text=false` - Get random article
  - Query parameters:
    - `include_text`: Include full text (default: false)

## Example Requests

```bash
# Search by title
curl "http://localhost:8002/api/v1/articles/search?q=Python&limit=5"

# Search by content
curl "http://localhost:8002/api/v1/articles/search?q=machine learning&search_type=content"

# Get specific article
curl "http://localhost:8002/api/v1/articles/Python?include_text=true"

# Get random article
curl "http://localhost:8002/api/v1/articles/random"

# Get stats
curl "http://localhost:8002/api/v1/statistics"

# Health check
curl "http://localhost:8002/api/v1/health"
```

## Response Format

All responses are JSON. Success returns data, errors return structured error messages:

```json
{
  "articles": [
    {
      "title": "Python",
      "text_length": 50000,
      "text": null
    }
  ],
  "total_count": 42,
  "limit": 20,
  "offset": 0
}
```

## Configuration

Edit `config.py` to customize:
- Database path
- Default limits
- Cache settings
- API metadata

## Project Structure

```
api/
├── main.py           # FastAPI application entry point
├── database.py       # DuckDB connection and query logic
├── models.py         # Pydantic response models
├── routes.py         # API endpoints
├── config.py         # Configuration settings
├── utils.py          # Helper utilities
├── requirements.txt  # Python dependencies
├── __init__.py       # Package initialization
└── README.md         # This file
```

## Architecture

### DatabaseManager
Handles all database operations:
- Connection pooling
- Search queries (title and content)
- Article retrieval
- Statistics

### Models
Type-safe request/response validation with Pydantic:
- `Article` - Single article with optional text
- `SearchResult` - Paginated search results
- `DatabaseStats` - Database statistics
- `HealthResponse` - API health status

### Routes
RESTful endpoints following standard conventions:
- Health checks
- Search functionality
- Single article retrieval
- Statistics

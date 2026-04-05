import duckdb
import polars as pl
from pathlib import Path
from tqdm import tqdm
from pprint import pprint

# Alternative: Load one batch at a time with progress tracking
data_dir = Path('/mnt/samsung/wiki-data-clean')
parquet_files = sorted(data_dir.glob('wiki_data_batch_*.parquet'))

print(f"Found {len(parquet_files)} parquet files")

# Connect to DuckDB
con = duckdb.connect('/home/steven/extraction-framework/wiki_data.duckdb', read_only=True)

# Verify total count
total = con.execute("SELECT COUNT(*) FROM wiki_articles").fetchone()[0]
print(f"\nTotal records in database: {total:,}")

# Create indexes on commonly queried columns
# Adjust column names based on your actual schema

# Index on title for fast lookups
#con.execute("CREATE INDEX IF NOT EXISTS idx_title ON wiki_articles(title)")

# Index on id if you have one
# con.execute("CREATE INDEX IF NOT EXISTS idx_id ON wiki_articles(id)")

#print("Indexes created successfully")

# Sample query: Get first 10 articles
# result = con.execute("SELECT * FROM wiki_articles LIMIT 10").pl()
# print("\nFirst 10 articles:")
# print(result)

# Search by title (example)
search_term = 'Natalie Portman'
result = con.execute(f"""
    SELECT title, text
    FROM wiki_articles 
    WHERE title LIKE '%{search_term}%' 
    LIMIT 20
""").pl()
print(f"\nSearch results for '{search_term}':")
print(result)

# Read first search result as dictionary/json
# if len(result) > 0:
#     first_entry = result.row(0, named=True)

#     print(f"\nFirst search result:")
#     pprint(first_entry)

# Get database statistics
# stats = con.execute("""
#     SELECT 
#         COUNT(*) as total_articles,
#         AVG(LENGTH(text)) as avg_text_length,
#         MAX(LENGTH(text)) as max_text_length,
#         MIN(LENGTH(text)) as min_text_length
#     FROM wiki_articles
# """).pl()
# print("\nDatabase statistics:")
# print(stats)

# Close connection when done
con.close()
print("Database connection closed")

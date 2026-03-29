import duckdb
import polars as pl
from pathlib import Path
from tqdm import tqdm

# Alternative: Load one batch at a time with progress tracking
data_dir = Path('/mnt/samsung/wiki-data-clean')
parquet_files = sorted(data_dir.glob('wiki_data_batch_*.parquet'))

print(f"Found {len(parquet_files)} parquet files")

# Connect to DuckDB
con = duckdb.connect('/home/steven/extraction-framework/wiki_data.duckdb')

# Check if table exists and determine where to resume
start_batch = 0
table_exists = False

try:
    current_count = con.execute("SELECT COUNT(*) FROM wiki_articles").fetchone()[0]
    table_exists = True
    print(f"Found existing table with {current_count:,} records")
    
    # Determine which batch to start from by comparing record counts
    if current_count > 0:
        cumulative_count = 0
        for i, parquet_file in enumerate(parquet_files):
            batch_count = len(pl.read_parquet(str(parquet_file)))
            cumulative_count += batch_count
            
            if cumulative_count == current_count:
                start_batch = i + 1
                print(f"Database contains batches 0-{i} ({cumulative_count:,} records)")
                print(f"Resuming from batch {start_batch}")
                break
            elif cumulative_count > current_count:
                print(f"Warning: Record count mismatch. Database has {current_count:,} records")
                print(f"But batches 0-{i-1} should have {cumulative_count - batch_count:,} records")
                print(f"Resuming from batch {i}")
                start_batch = i
                break
        
        if cumulative_count < current_count:
            print(f"Warning: Database has more records ({current_count:,}) than all batches ({cumulative_count:,})")
            print("All batches appear to be loaded already")
            start_batch = len(parquet_files)
        elif start_batch == 0 and cumulative_count == current_count:
            # All batches loaded
            start_batch = len(parquet_files)
            print("All batches already loaded!")
    else:
        print("Table exists but is empty. Starting from batch 0")
        start_batch = 0
        
except:
    # Table doesn't exist, create it
    print("No existing table found. Creating new table...")
    first_df = pl.read_parquet(str(parquet_files[0]))
    con.execute("CREATE TABLE wiki_articles AS SELECT * FROM first_df")
    print(f"Created table with batch 0: {len(first_df):,} records")
    start_batch = 1

# Insert remaining batches
if start_batch < len(parquet_files):
    print(f"\nLoading batches {start_batch} to {len(parquet_files)-1}")
    for i in tqdm(range(start_batch, len(parquet_files)), desc="Loading batches"):
        df_batch = pl.read_parquet(str(parquet_files[i]))
        con.execute("INSERT INTO wiki_articles SELECT * FROM df_batch")
else:
    print("\nNo new batches to load.")

# Verify total count
total = con.execute("SELECT COUNT(*) FROM wiki_articles").fetchone()[0]
print(f"\nTotal records in database: {total:,}")

# Create indexes on commonly queried columns
# Adjust column names based on your actual schema

# Index on title for fast lookups
con.execute("CREATE INDEX IF NOT EXISTS idx_title ON wiki_articles(title)")

# Index on id if you have one
# con.execute("CREATE INDEX IF NOT EXISTS idx_id ON wiki_articles(id)")

print("Indexes created successfully")

# Sample query: Get first 10 articles
result = con.execute("SELECT * FROM wiki_articles LIMIT 10").pl()
print("\nFirst 10 articles:")
print(result)

# Search by title (example)
search_term = 'Python'
result = con.execute(f"""
    SELECT title, LENGTH(text) as text_length 
    FROM wiki_articles 
    WHERE title LIKE '%{search_term}%' 
    LIMIT 20
""").pl()
print(f"\nSearch results for '{search_term}':")
print(result)

# Get database statistics
stats = con.execute("""
    SELECT 
        COUNT(*) as total_articles,
        AVG(LENGTH(text)) as avg_text_length,
        MAX(LENGTH(text)) as max_text_length,
        MIN(LENGTH(text)) as min_text_length
    FROM wiki_articles
""").pl()
print("\nDatabase statistics:")
print(stats)

# Close connection when done
con.close()
print("Database connection closed")

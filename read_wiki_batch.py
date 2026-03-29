#!/usr/bin/env python3
import polars as pl

# Read the first batch parquet file
file_path = "/mnt/samsung/wiki-data/wiki_data_batch_00001.parquet"
df = pl.read_parquet(file_path)

# Display the top 100 records
print(f"Total records in batch 1: {len(df)}")
print(f"\nTop 100 records:\n")
print(df.head(100))

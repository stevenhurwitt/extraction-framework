#!/usr/bin/env python3
"""
Clean Wikipedia data by filtering out redirect pages.
Reads all batch parquet files and removes entries with #REDIRECT in text column.
"""

import polars as pl
from pathlib import Path
from glob import glob

def clean_wiki_data(input_dir: str, output_dir: str):
    """
    Read all Wikipedia batch files and filter out redirect pages.
    
    Args:
        input_dir: Directory containing wiki_data_batch_*.parquet files
        output_dir: Directory to write cleaned parquet files
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all batch files
    pattern = str(input_path / "wiki_data_batch_*.parquet")
    batch_files = sorted(glob(pattern))
    
    if not batch_files:
        print(f"No batch files found matching: {pattern}")
        return
    
    print(f"Found {len(batch_files)} batch files")
    print(f"Output directory: {output_path}")
    print("-" * 60)
    
    total_original = 0
    total_cleaned = 0
    total_redirects = 0
    
    for batch_file in batch_files:
        batch_name = Path(batch_file).name
        print(f"\nProcessing: {batch_name}")
        
        # Read the batch
        df = pl.read_parquet(batch_file)
        original_count = len(df)
        total_original += original_count
        
        # Filter out redirects
        # Remove rows where text column contains "#REDIRECT"
        df_clean = df.filter(~pl.col("text").str.contains("#REDIRECT"))
        
        cleaned_count = len(df_clean)
        redirects_removed = original_count - cleaned_count
        total_cleaned += cleaned_count
        total_redirects += redirects_removed
        
        # Write cleaned data
        output_file = output_path / batch_name
        df_clean.write_parquet(output_file)
        
        print(f"  Original rows: {original_count:,}")
        print(f"  Redirects removed: {redirects_removed:,}")
        print(f"  Cleaned rows: {cleaned_count:,}")
        print(f"  Written to: {output_file}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total batches processed: {len(batch_files)}")
    print(f"Total original rows: {total_original:,}")
    print(f"Total redirects removed: {total_redirects:,}")
    print(f"Total cleaned rows: {total_cleaned:,}")
    print(f"Percentage retained: {100 * total_cleaned / total_original:.2f}%")
    print(f"\n✓ Done! Cleaned data written to: {output_path}")


if __name__ == "__main__":
    # Input directory containing raw batch files
    input_directory = "/mnt/samsung/wiki-data/"
    
    # Output directory for cleaned files
    output_directory = "/mnt/samsung/wiki-data-clean/"
    
    clean_wiki_data(input_directory, output_directory)

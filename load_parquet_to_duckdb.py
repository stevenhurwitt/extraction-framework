#!/usr/bin/env python3
"""
Load batches of enwiki parquet files into a DuckDB database.

Features:
- Resumable: tracks loaded files in a `loaded_batches` table, skips them on re-run.
- One transaction per batch file, so a crash only loses the current batch.
- Streams each Parquet file directly into DuckDB; no file is loaded into Python memory.
- Progress bar with tqdm.

Usage:
    python load_parquet_to_duckdb.py
    python load_parquet_to_duckdb.py --db /mnt/lacie/wiki-data-2026/wiki_data_2026.duckdb
    python load_parquet_to_duckdb.py --data-dir /mnt/lacie/wiki-data-2026/enwiki/data
"""

import argparse
import sys
from pathlib import Path

import duckdb
from tqdm import tqdm


def parse_args():
    p = argparse.ArgumentParser(description="Load enwiki parquet batches into DuckDB")
    p.add_argument(
        "--db",
        default="/home/steven/extraction-framework/wiki_data_2026.duckdb",
        help="Path to the DuckDB database file (default: on the Lacie drive)",
    )
    p.add_argument(
        "--data-dir",
        default="/mnt/lacie/wiki-data-2026/enwiki/data",
        help="Directory containing the parquet batch files",
    )
    p.add_argument(
        "--glob",
        default="enwiki_namespace_0_*.parquet",
        help="Glob pattern for batch files within the data dir",
    )
    p.add_argument(
        "--table",
        default="wiki_articles",
        help="Target table name",
    )
    p.add_argument(
        "--memory-limit",
        default="8GB",
        help="Maximum memory DuckDB may use before spilling to disk (default: 8GB)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    data_dir = Path(args.data_dir)
    parquet_files = sorted(data_dir.glob(args.glob))

    if not parquet_files:
        sys.exit(f"No parquet files matching '{args.glob}' found in {data_dir}")

    print(f"Found {len(parquet_files)} parquet files in {data_dir}")
    print(f"Database: {args.db}")

    con = duckdb.connect(args.db)
    try:
        # Bound memory usage; DuckDB spills to disk instead of holding a file in RAM.
        con.execute(f"SET memory_limit = '{args.memory_limit}'")

        # Create the target table with the correct schema if it doesn't exist yet.
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {args.table} AS
            SELECT * FROM read_parquet('{parquet_files[0]}') LIMIT 0
        """)

        # Unique index on identifier: makes the anti-join below fast and
        # guarantees the same article can never be inserted twice.
        con.execute(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_{args.table}_identifier
            ON {args.table}(identifier)
        """)

        # Bookkeeping table for resumability.
        con.execute("""
            CREATE TABLE IF NOT EXISTS loaded_batches (
                file_name VARCHAR PRIMARY KEY,
                row_count BIGINT,
                loaded_at TIMESTAMP DEFAULT current_timestamp
            )
        """)

        already_loaded = {
            row[0]
            for row in con.execute("SELECT file_name FROM loaded_batches").fetchall()
        }
        if already_loaded:
            print(
                f"Resuming: {len(already_loaded)} batches already loaded, skipping them."
            )

        todo = [f for f in parquet_files if f.name not in already_loaded]
        print(f"{len(todo)} batches to load.")

        for f in tqdm(todo, desc="Loading batches", unit="batch"):
            try:
                con.execute("BEGIN TRANSACTION")
                before = con.execute(f"SELECT COUNT(*) FROM {args.table}").fetchone()[0]
                # read_parquet streams this file through DuckDB's execution engine.
                # Once execute() returns, its scan buffers are no longer retained.
                con.execute(f"""
                    INSERT INTO {args.table}
                    SELECT src.* FROM read_parquet('{f}') src
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {args.table} wa
                        WHERE wa.identifier = src.identifier
                    )
                """)
                after = con.execute(f"SELECT COUNT(*) FROM {args.table}").fetchone()[0]
                con.execute(
                    "INSERT INTO loaded_batches (file_name, row_count) VALUES (?, ?)",
                    [f.name, after - before],
                )
                con.execute("COMMIT")
                # Persist this batch and discard its WAL before moving to the next file.
                con.execute("CHECKPOINT")
            except Exception as e:
                con.execute("ROLLBACK")
                print(f"\nFailed on {f.name}: {e}")
                print(
                    "Fix the issue and re-run — already committed batches will be skipped."
                )
                sys.exit(1)

        grand_total = con.execute(f"SELECT COUNT(*) FROM {args.table}").fetchone()[0]
        loaded = con.execute(
            "SELECT COALESCE(SUM(row_count), 0) FROM loaded_batches"
        ).fetchone()[0]
        print(f"\nDone. Rows inserted across all tracked batches: {loaded:,}")
        print(f"Total rows in '{args.table}': {grand_total:,}")
    finally:
        con.close()


if __name__ == "__main__":
    main()

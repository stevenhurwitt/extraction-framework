#!/usr/bin/env python3
"""Create indexes on the wiki_data_2026.duckdb database.

Creates:
  - idx_wiki_articles_name: B-tree index on `name` (speeds up exact title lookups)
  - FTS index on (name, abstract): enables full-text search via match_bm25()

The database must not be opened read-only elsewhere (e.g. stop the API container
first), since DuckDB requires exclusive write access.

Usage:
    python create_indexes.py
    python create_indexes.py --db /mnt/lacie/wiki-data-2026/wiki_data_2026.duckdb
"""

import argparse
import time

import duckdb


def parse_args():
    p = argparse.ArgumentParser(description="Create indexes on the wiki DuckDB database")
    p.add_argument(
        "--db",
        default="/home/steven/extraction-framework/wiki_data_2026.duckdb",
        help="Path to the DuckDB database file",
    )
    p.add_argument(
        "--table",
        default="wiki_articles",
        help="Target table name",
    )
    p.add_argument(
        "--memory-limit",
        default="8GB",
        help="DuckDB memory limit (default: 8GB)",
    )
    p.add_argument(
        "--skip-fts",
        action="store_true",
        help="Skip creating the full-text search index (it takes the longest)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    con = duckdb.connect(args.db)
    try:
        con.execute(f"SET memory_limit = '{args.memory_limit}'")

        # B-tree index for exact-match lookups by article title.
        t0 = time.time()
        print(f"Creating index on {args.table}(name) ...")
        con.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{args.table}_name ON {args.table}(name)"
        )
        print(f"  done in {time.time() - t0:.1f}s")

        # Full-text search index over title + abstract. Query it with:
        #   SELECT name, fts_main_wiki_articles.match_bm25(identifier, 'query') AS score
        #   FROM wiki_articles WHERE score IS NOT NULL ORDER BY score DESC;
        if not args.skip_fts:
            t0 = time.time()
            print(f"Creating FTS index on {args.table}(name, abstract) ...")
            con.execute("INSTALL fts; LOAD fts;")
            con.execute(
                f"PRAGMA create_fts_index('{args.table}', 'identifier', "
                "'name', 'abstract', overwrite=1)"
            )
            print(f"  done in {time.time() - t0:.1f}s")

        print("\nAll indexes created.")
    finally:
        con.close()


if __name__ == "__main__":
    main()

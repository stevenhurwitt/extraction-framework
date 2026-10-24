#!/usr/bin/env python3
"""Run a battery of useful queries against the enwiki data in DuckDB.

DuckDB port of run_enwiki_queries.py (Trino). Queries the wiki_articles
table in wiki_data_2026.duckdb.

Usage (from the repo root, using the uv virtual environment):
    .venv/bin/python trino/run_enwiki_queries_duckdb.py
    .venv/bin/python trino/run_enwiki_queries_duckdb.py --only count,recent
    .venv/bin/python trino/run_enwiki_queries_duckdb.py --list
    .venv/bin/python trino/run_enwiki_queries_duckdb.py --prepare  # one-time: adds ref_count column
"""

import argparse
import sys
import time

import duckdb

MAX_CELL_WIDTH = 50

# DuckDB equivalents of the queries in trino/enwiki_queries.sql:
#   cardinality("references")  -> len("references")
#   version.editor.name etc.   -> same struct dot-access works in DuckDB
#   date_trunc('month', ts)    -> same
QUERIES = {
    "count": (
        "Total articles in wiki_articles",
        "SELECT COUNT(*) AS total_articles FROM wiki_articles",
    ),
    "sample": (
        "Sample of articles",
        """SELECT identifier, name, description, date_modified
           FROM wiki_articles LIMIT 100""",
    ),
    "recent": (
        "Most recently modified articles",
        """SELECT name, date_modified, version.editor.name AS editor
           FROM wiki_articles ORDER BY date_modified DESC LIMIT 100""",
    ),
    "largest": (
        "Largest articles by character count",
        """SELECT name, version.number_of_characters AS chars
           FROM wiki_articles ORDER BY chars DESC LIMIT 100""",
    ),
    "editors": (
        "Most prolific editors",
        """SELECT version.editor.name AS editor, COUNT(*) AS edits
           FROM wiki_articles GROUP BY 1 ORDER BY edits DESC LIMIT 100""",
    ),
    "revert_risk": (
        "Articles predicted to be reverted (revertrisk model)",
        """SELECT name, version.scores.revertrisk.probability."true" AS revert_prob
           FROM wiki_articles WHERE version.scores.revertrisk.prediction = true
           ORDER BY revert_prob DESC LIMIT 100""",
    ),
    "reference_need": (
        "Articles most in need of references",
        """SELECT name, version.scores.referenceneed.reference_need_score AS need_score
           FROM wiki_articles ORDER BY need_score DESC LIMIT 10""",
    ),
    "editor_types": (
        "Edits by admin / anonymous status",
        """SELECT version.editor.is_admin, version.editor.is_anonymous, COUNT(*) AS articles
           FROM wiki_articles GROUP BY 1, 2 ORDER BY articles DESC""",
    ),
    "flagged": (
        "Breaking-news / flagged articles",
        """SELECT name, version.is_breaking_news, version.is_flagged_stable, version.noindex
           FROM wiki_articles
           WHERE version.is_breaking_news = true
              OR version.is_flagged_stable = true
              OR version.noindex = true
           LIMIT 100""",
    ),
    "name_search": (
        "Full-text search on article names (e.g. 'kanye west')",
        """SELECT identifier, name, description
           FROM wiki_articles
           WHERE lower(name) LIKE '%kanye west%'
           LIMIT 100""",
    ),
    "most_refs": (
        "Articles with the most references",
        # Uses the materialized ref_count column (run --prepare first);
        # falls back to computing len("references") if it doesn't exist.
        """SELECT name, ref_count FROM wiki_articles
           ORDER BY ref_count DESC LIMIT 100""",
    ),
    "per_month": (
        "Articles created per month",
        """SELECT date_trunc('month', date_created) AS month, COUNT(*) AS articles
           FROM wiki_articles
           GROUP BY 1 ORDER BY 1 DESC LIMIT 24""",
    ),
}


def prepare(db_path):
    """One-time setup: materialize len("references") into a ref_count column.

    Computing len() over the nested references list for every article is the
    slow part of the 'most_refs' query; a plain integer column lets DuckDB
    scan a single small column instead. Requires write access to the DB.
    """
    conn = duckdb.connect(db_path)
    with conn:
        cols = {row[0] for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'wiki_articles'").fetchall()}
        if "ref_count" in cols:
            print("ref_count column already exists; nothing to do.")
            return
        print("Adding ref_count column...")
        conn.execute("ALTER TABLE wiki_articles ADD COLUMN ref_count INTEGER")
        start = time.monotonic()
        conn.execute('UPDATE wiki_articles SET ref_count = len("references")')
        print(f"Populated ref_count in {time.monotonic() - start:.2f}s.")


def fmt(value):
    if value is None:
        return "NULL"
    text = str(value).replace("\n", " ")
    return text[: MAX_CELL_WIDTH - 3] + "..." if len(text) > MAX_CELL_WIDTH else text


def print_table(columns, rows):
    formatted = [[fmt(v) for v in row] for row in rows]
    widths = [
        max(len(col), *(len(r[i]) for r in formatted)) if formatted else len(col)
        for i, col in enumerate(columns)
    ]
    print(" | ".join(c.ljust(widths[i]) for i, c in enumerate(columns)))
    print("-+-".join("-" * w for w in widths))
    for row in formatted:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    print(f"({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Comma-separated query names to run (default: all)")
    parser.add_argument("--list", action="store_true", help="List available queries and exit")
    parser.add_argument("--db", default="/home/steven/extraction-framework/wiki_data_2026.duckdb", help="Path to DuckDB file")
    parser.add_argument("--prepare", action="store_true",
                        help="Materialize helper columns (ref_count) to speed up queries, then exit")
    args = parser.parse_args()

    if args.prepare:
        prepare(args.db)
        return

    if args.list:
        for key, (title, _) in QUERIES.items():
            print(f"{key:15s} {title}")
        return

    selected = list(QUERIES)
    if args.only:
        selected = [s.strip() for s in args.only.split(",")]
        unknown = [s for s in selected if s not in QUERIES]
        if unknown:
            sys.exit(f"Unknown queries: {unknown}. Use --list to see options.")

    conn = duckdb.connect(args.db, read_only=True)
    with conn:
        cols = {row[0] for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'wiki_articles'").fetchall()}
        if "most_refs" in selected and "ref_count" not in cols:
            print("(note: ref_count column missing; run with --prepare once to speed up most_refs)")
            QUERIES["most_refs"] = (
                QUERIES["most_refs"][0],
                """SELECT name, len("references") AS ref_count
                   FROM wiki_articles ORDER BY ref_count DESC LIMIT 100""",
            )
        for key in selected:
            title, sql = QUERIES[key]
            print(f"\n=== [{key}] {title} ===")
            start = time.monotonic()
            try:
                result = conn.execute(sql)
                columns = [d[0] for d in result.description or []]
                rows = result.fetchall()
            except duckdb.Error as exc:
                print(f"  Query failed: {exc}")
                continue
            print_table(columns, rows)
            print(f"({time.monotonic() - start:.2f}s)")


if __name__ == "__main__":
    main()

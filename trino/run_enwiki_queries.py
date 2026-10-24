#!/usr/bin/env python3
"""Run a battery of useful queries against the Trino enwiki table.

Usage (from the repo root, using the uv virtual environment):
    .venv/bin/python trino/run_enwiki_queries.py
    .venv/bin/python trino/run_enwiki_queries.py --only count,recent
    .venv/bin/python trino/run_enwiki_queries.py --list
"""

import argparse
import sys
import time

from trino.dbapi import connect
from trino.exceptions import TrinoConnectionError, TrinoQueryError

MAX_CELL_WIDTH = 50

QUERIES = {
    "count": (
        "Total articles in enwiki",
        "SELECT COUNT(*) AS total_articles FROM enwiki",
    ),
    "recent": (
        "Most recently modified articles",
        """SELECT name, date_modified, version.editor.name AS editor
           FROM enwiki ORDER BY date_modified DESC LIMIT 10""",
    ),
    "largest": (
        "Largest articles by character count",
        """SELECT name, version.number_of_characters AS chars
           FROM enwiki ORDER BY chars DESC LIMIT 10""",
    ),
    "editors": (
        "Most prolific editors",
        """SELECT version.editor.name AS editor, COUNT(*) AS edits
           FROM enwiki GROUP BY 1 ORDER BY edits DESC LIMIT 10""",
    ),
    "revert_risk": (
        "Articles predicted to be reverted (revertrisk model)",
        """SELECT name, version.scores.revertrisk.probability."true" AS revert_prob
           FROM enwiki WHERE version.scores.revertrisk.prediction = true
           ORDER BY revert_prob DESC LIMIT 10""",
    ),
    "reference_need": (
        "Articles most in need of references",
        """SELECT name, version.scores.referenceneed.reference_need_score AS need_score
           FROM enwiki ORDER BY need_score DESC LIMIT 10""",
    ),
    "editor_types": (
        "Edits by admin / anonymous status",
        """SELECT version.editor.is_admin, version.editor.is_anonymous, COUNT(*) AS articles
           FROM enwiki GROUP BY 1, 2 ORDER BY articles DESC""",
    ),
    "most_refs": (
        "Articles with the most references",
        """SELECT name, cardinality("references") AS ref_count
           FROM enwiki ORDER BY ref_count DESC LIMIT 10""",
    ),
}


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
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--user", default="trino")
    parser.add_argument("--catalog", default="wiki")
    parser.add_argument("--schema", default="default")
    args = parser.parse_args()

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

    try:
        conn = connect(
            host=args.host, port=args.port, user=args.user,
            catalog=args.catalog, schema=args.schema,
        )
    except TrinoConnectionError as exc:
        sys.exit(f"Could not connect to Trino at {args.host}:{args.port}: {exc}")

    with conn:
        cur = conn.cursor()
        for key in selected:
            title, sql = QUERIES[key]
            print(f"\n=== [{key}] {title} ===")
            start = time.monotonic()
            try:
                cur.execute(sql)
                columns = [d[0] for d in cur.description or []]
                rows = cur.fetchall()
            except TrinoQueryError as exc:
                print(f"  Query failed: {exc.message}")
                continue
            print_table(columns, rows)
            print(f"({time.monotonic() - start:.2f}s)")


if __name__ == "__main__":
    main()

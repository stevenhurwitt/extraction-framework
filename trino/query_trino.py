#!/usr/bin/env python3
"""Query the Trino data lake (wiki catalog).

Examples:
    python query_trino.py                          # sample rows from enwiki
    python query_trino.py --tables                 # list tables
    python query_trino.py --describe enwiki        # show table columns
    python query_trino.py -q "SELECT name FROM enwiki WHERE identifier = 12"
    python query_trino.py -f query.sql --format csv
    cat query.sql | python query_trino.py          # read SQL from stdin
"""

import argparse
import json
import sys

from trino.dbapi import connect
from trino.exceptions import TrinoQueryError, TrinoConnectionError

DEFAULT_QUERY = "SELECT identifier, name, date_modified FROM enwiki LIMIT %(limit)s"
MAX_CELL_WIDTH = 60


def get_connection(args):
    return connect(
        host=args.host,
        port=args.port,
        user=args.user,
        catalog=args.catalog,
        schema=args.schema,
    )


def fetch(cur, sql):
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description or []]
    rows = cur.fetchall()
    return columns, rows


def print_table(columns, rows):
    """Print rows as an aligned text table, truncating wide cells."""
    def fmt(value):
        if value is None:
            return "NULL"
        text = str(value).replace("\n", " ")
        if len(text) > MAX_CELL_WIDTH:
            text = text[: MAX_CELL_WIDTH - 3] + "..."
        return text

    formatted = [[fmt(v) for v in row] for row in rows]
    widths = [
        max(len(col), *(len(row[i]) for row in formatted)) if formatted else len(col)
        for i, col in enumerate(columns)
    ]
    header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    print(header)
    print("-+-".join("-" * w for w in widths))
    for row in formatted:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    print(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")


def print_rows(columns, rows, output_format):
    if output_format == "json":
        json.dump([dict(zip(columns, map(str, row))) for row in rows], sys.stdout, indent=2, default=str)
        print()
    elif output_format == "csv":
        import csv

        writer = csv.writer(sys.stdout)
        writer.writerow(columns)
        writer.writerows(rows)
    else:
        print_table(columns, rows)


def main():
    parser = argparse.ArgumentParser(description="Query the Trino data lake.")
    parser.add_argument("query", nargs="?", help="SQL query to run (omit to read stdin or run a sample query)")
    parser.add_argument("-f", "--file", help="Read SQL from a file")
    parser.add_argument("-q", "--sql", help="SQL query string (alternative to positional arg)")
    parser.add_argument("--tables", action="store_true", help="List tables in the catalog/schema")
    parser.add_argument("--describe", metavar="TABLE", help="Describe a table's columns")
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table", help="Output format")
    parser.add_argument("--limit", type=int, default=20, help="Row limit for the default sample query")
    parser.add_argument("--host", default="localhost", help="Trino host (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="Trino port (default: 8080)")
    parser.add_argument("--user", default="trino", help="Trino user (default: trino)")
    parser.add_argument("--catalog", default="wiki", help="Catalog (default: wiki)")
    parser.add_argument("--schema", default="default", help="Schema (default: default)")
    args = parser.parse_args()

    if args.tables:
        sql = "SHOW TABLES"
    elif args.describe:
        sql = f"DESCRIBE {args.describe}"
    elif args.file:
        with open(args.file) as fh:
            sql = fh.read()
    elif args.sql:
        sql = args.sql
    elif args.query:
        sql = args.query
    elif not sys.stdin.isatty():
        sql = sys.stdin.read()
    else:
        sql = DEFAULT_QUERY % {"limit": args.limit}

    try:
        conn = get_connection(args)
    except TrinoConnectionError as exc:
        sys.exit(f"Could not connect to Trino at {args.host}:{args.port}: {exc}")

    try:
        with conn:
            cur = conn.cursor()
            columns, rows = fetch(cur, sql)
    except TrinoQueryError as exc:
        sys.exit(f"Query failed: {exc.message}")
    except KeyboardInterrupt:
        sys.exit("Cancelled.")

    if not columns:
        print("Query executed successfully (no result set).")
        return
    print_rows(columns, rows, args.format)


if __name__ == "__main__":
    main()

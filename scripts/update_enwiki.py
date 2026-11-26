#!/usr/bin/env python3
"""Incrementally update the enwiki data lake from the Wikimedia Enterprise API.

Strategy: query the (free) MediaWiki recentchanges feed for English Wikipedia
articles changed since the last run, fetch the full structured payload for each
changed article from the Enterprise On-demand API, and write a delta Parquet
file per run into <data_dir>/../updates/.

Auth: reads creds.json. If it contains "username" and "password" the script
logs in and auto-refreshes tokens (required for cron, since dashboard API keys
expire after 24h). Otherwise it falls back to "wikipedia_api_key".

Free-tier limits handled here: 10 req/s (we throttle to ~8), monthly on-demand
quota (tracked in the state file, run aborts when --monthly-cap is reached),
429/401 retry with backoff.

Usage:
    python3 update_enwiki.py --data-dir /mnt/lacie/enwiki/data
    python3 update_enwiki.py --data-dir /mnt/lacie/enwiki/data \
        --data-dir /mnt/lacie/wiki-data-2026/enwiki/data --dry-run
"""

import argparse
import datetime as dt
import json
import logging
import sys
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import requests

ENTERPRISE_API = "https://api.enterprise.wikimedia.com/v2"
ENTERPRISE_AUTH = "https://auth.enterprise.wikimedia.com/v1"
MEDIAWIKI_API = "https://en.wikipedia.org/w/api.php"

RATE_LIMIT_DELAY = 0.125  # ~8 requests/second, free tier allows 10

log = logging.getLogger("update_enwiki")


class EnterpriseClient:
    def __init__(self, creds_path: Path):
        creds = json.loads(creds_path.read_text())
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        user = creds.get("wikipedia_user") or creds.get("username")
        pw = creds.get("wikipedia_password") or creds.get("password")
        if user and pw:
            self._login(user, pw)
        elif creds.get("wikipedia_api_key"):
            self.access_token = creds["wikipedia_api_key"]
            log.warning("Using static wikipedia_api_key; it expires 24h after issue. "
                        "Add \"username\"/\"password\" to creds.json for auto-refresh.")
        else:
            raise SystemExit("creds.json needs username/password or wikipedia_api_key")

    def _login(self, username, password):
        r = self.session.post(f"{ENTERPRISE_AUTH}/login",
                              json={"username": username, "password": password}, timeout=30)
        r.raise_for_status()
        data = r.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        log.info("Logged in to Wikimedia Enterprise as %s", username)

    def _refresh(self):
        if not self.refresh_token:
            raise RuntimeError("Token expired and no refresh token available")
        r = self.session.post(f"{ENTERPRISE_AUTH}/token-refresh",
                              json={"refresh_token": self.refresh_token}, timeout=30)
        r.raise_for_status()
        self.access_token = r.json()["access_token"]
        log.info("Refreshed Enterprise access token")

    def get_article(self, name: str):
        """Fetch one article's structured payload; returns dict or None."""
        url = f"{ENTERPRISE_API}/articles/{requests.utils.quote(name, safe='')}"
        body = {"filters": [{"field": "is_part_of.identifier", "value": "enwiki"}]}
        for attempt in range(5):
            r = self.session.post(url, json=body, timeout=60,
                                  headers={"Authorization": f"Bearer {self.access_token}"})
            if r.status_code == 401 and attempt == 0 and self.refresh_token:
                self._refresh()
                continue
            if r.status_code == 404:
                return None  # deleted/redirected away
            if r.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                log.warning("429 rate-limited; sleeping %ss", wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            results = r.json()
            return results[0] if results else None
        raise RuntimeError(f"Giving up on {name!r} after retries")


def fetch_changed_titles(since: dt.datetime, until: dt.datetime):
    """ns-0 pages edited/created on en.wikipedia between since and until.

    Returns {title: most recent change timestamp (UTC)}."""
    titles, cont = {}, {}
    session = requests.Session()
    while True:
        params = {
            "action": "query", "format": "json", "list": "recentchanges",
            "rcnamespace": 0, "rctype": "edit|new", "rcprop": "title|timestamp",
            "rclimit": "max",
            "rcstart": until.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rcend": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            **cont,
        }
        for attempt in range(5):
            r = session.get(MEDIAWIKI_API, params=params, timeout=30,
                            headers={"User-Agent": "enwiki-lake-updater/1.0 (research)"})
            if r.status_code == 429:
                wait = min(2 ** attempt * 10, 120)
                log.warning("MediaWiki 429; sleeping %ss", wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            break
        else:
            raise RuntimeError("MediaWiki recentchanges still failing after retries")
        data = r.json()
        time.sleep(0.5)
        for rc in data["query"]["recentchanges"]:
            ts = dt.datetime.strptime(rc["timestamp"], "%Y-%m-%dT%H:%M:%SZ") \
                .replace(tzinfo=dt.timezone.utc)
            if rc["title"] not in titles or ts > titles[rc["title"]]:
                titles[rc["title"]] = ts
        if "continue" not in data:
            return titles
        cont = data["continue"]


def _parse_ts(value):
    if isinstance(value, str):
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return value


def _coerce(value, typ: pa.DataType):
    """Coerce an API JSON value to the lake schema type."""
    if value is None:
        return None
    if pa.types.is_struct(typ):
        if not isinstance(value, dict):
            return None
        return {f.name: _coerce(value.get(f.name), f.type) for f in typ}
    if pa.types.is_list(typ):
        if not isinstance(value, list):
            return None
        return [_coerce(v, typ.value_type) for v in value]
    if pa.types.is_timestamp(typ):
        return _parse_ts(value)
    if pa.types.is_integer(typ):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if pa.types.is_floating(typ):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if pa.types.is_boolean(typ):
        return bool(value)
    if pa.types.is_string(typ):
        # complex fields stored as JSON strings (infoboxes, sections, tables, ...)
        return value if isinstance(value, str) else json.dumps(value)
    return value


def normalize(article: dict, schema: pa.Schema) -> dict:
    """Project an API article onto the lake schema, coercing types."""
    return {f.name: _coerce(article.get(f.name), f.type) for f in schema}


def to_parquet(articles, schema: pa.Schema, out_path: Path):
    rows = [normalize(a, schema) for a in articles]
    table = pa.Table.from_pylist(rows, schema=schema)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path, compression="zstd")
    log.info("Wrote %d rows to %s", table.num_rows, out_path)


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", action="append", required=True,
                    help="Lake data dir (repeatable); first one provides the Parquet schema")
    ap.add_argument("--updates-dir", action="append",
                    help="Where to write delta Parquet files (repeatable). "
                         "Default: <data-dir>/../updates for each --data-dir")
    ap.add_argument("--creds", type=Path, default=Path(__file__).resolve().parents[1] / "creds.json")
    ap.add_argument("--state", type=Path,
                    default=Path.home() / ".enwiki_update_state.json")
    ap.add_argument("--monthly-cap", type=int, default=45_000,
                    help="Abort when monthly on-demand requests would exceed this")
    ap.add_argument("--max-articles", type=int, default=20_000,
                    help="Cap on articles fetched per run")
    ap.add_argument("--dry-run", action="store_true",
                    help="List changed titles without calling the Enterprise API")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    state = load_state(args.state)
    month = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
    if state.get("usage_month") != month:
        state["usage_month"], state["monthly_requests"] = month, 0

    until = dt.datetime.now(dt.timezone.utc)
    since = dt.datetime.fromisoformat(state["last_run"]) if state.get("last_run") \
        else until - dt.timedelta(days=1)
    log.info("Collecting changes from %s to %s", since.isoformat(), until.isoformat())

    changed = fetch_changed_titles(since, until)
    titles = sorted(changed, key=changed.get, reverse=True)  # most recent first
    log.info("%d articles changed", len(titles))
    if args.dry_run:
        print("\n".join(titles))
        return

    budget = min(args.max_articles, args.monthly_cap - state["monthly_requests"])
    if budget <= 0:
        log.error("Monthly request budget exhausted (%d used)", state["monthly_requests"])
        sys.exit(1)
    capped = len(titles) > budget
    if capped:
        log.warning("Capping this run at %d of %d changed articles (most recent first)",
                    budget, len(titles))
        titles = titles[:budget]

    client = EnterpriseClient(args.creds)
    schema = pq.read_schema(Path(args.data_dir[0]) / "enwiki_namespace_0_00000.parquet")

    fetched, missing = [], 0
    for i, title in enumerate(titles, 1):
        try:
            article = client.get_article(title)
        except Exception:
            log.exception("Failed to fetch %r; skipping", title)
            missing += 1
            continue
        state["monthly_requests"] += 1
        if i % 25 == 0:  # persist usage incrementally so crashes don't lose it
            save_state(args.state, state)
        if article is None:
            missing += 1
        else:
            fetched.append(article)
        if i % 500 == 0:
            log.info("Progress: %d/%d fetched, %d missing", i, len(titles), missing)
        time.sleep(RATE_LIMIT_DELAY)

    if fetched:
        stamp = until.strftime("%Y%m%dT%H%M%SZ")
        out_dirs = [Path(d) for d in args.updates_dir] if args.updates_dir \
            else [Path(d).parent / "updates" for d in args.data_dir]
        for out_dir in out_dirs:
            to_parquet(fetched, schema, out_dir / f"enwiki_updates_{stamp}.parquet")

    if capped and titles:
        # Older unfetched changes fall behind the cursor; next run won't rescan them.
        oldest_fetched = min(changed[t] for t in titles)
        state["last_run"] = oldest_fetched.isoformat()
        log.info("Skipped %d older changes; cursor advanced to %s",
                 len(changed) - len(titles), state["last_run"])
    else:
        state["last_run"] = until.isoformat()
    save_state(args.state, state)
    log.info("Done: %d updated, %d missing, %d requests used this month",
             len(fetched), missing, state["monthly_requests"])


if __name__ == "__main__":
    main()

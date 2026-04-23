#!/usr/bin/env python3
"""
Create, execute, and validate the USTB Dune queries via the Dune API.

Usage:
    export DUNE_API_KEY=...
    python scripts/build_dune_dashboard.py

What it does:
  1. Reads every SQL file in ../sql/
  2. Creates a saved query in Dune for each
  3. Executes the validation scalar query synchronously
  4. Prints query IDs + URLs plus the validation numbers (target ~65.3M / ~99)

What it does NOT do:
  - Create the dashboard itself. Dune's dashboard-creation endpoints are
    unstable / partially unavailable via public API. After this script runs,
    open https://dune.com/browse/dashboards, click "New dashboard", and add
    each query's saved visualization.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib import request, error

API_BASE = "https://api.dune.com/api/v1"
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def api_key() -> str:
    key = os.environ.get("DUNE_API_KEY")
    if not key:
        sys.exit("DUNE_API_KEY env var is required")
    return key


def call(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = request.Request(
        url,
        data=data,
        method=method,
        headers={
            "x-dune-api-key": api_key(),
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read() or b"{}")
    except error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')}")


def create_query(name: str, sql: str) -> int:
    resp = call("POST", "/query", {
        "name": name,
        "query_sql": sql,
        "is_private": False,
    })
    return int(resp["query_id"])


def execute_and_wait(query_id: int, poll_seconds: float = 2.0, timeout_seconds: float = 300) -> dict:
    exec_resp = call("POST", f"/query/{query_id}/execute")
    execution_id = exec_resp["execution_id"]
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        status = call("GET", f"/execution/{execution_id}/status")
        state = status.get("state", "")
        if state == "QUERY_STATE_COMPLETED":
            return call("GET", f"/execution/{execution_id}/results")
        if state in {"QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"}:
            sys.exit(f"Query {query_id} ended in state {state}: {status}")
        time.sleep(poll_seconds)
    sys.exit(f"Query {query_id} timed out after {timeout_seconds}s")


def main() -> None:
    files = sorted(SQL_DIR.glob("*.sql"))
    if not files:
        sys.exit(f"No SQL files found in {SQL_DIR}")

    created: list[tuple[str, int]] = []
    validation_query_id: int | None = None

    for f in files:
        sql = f.read_text()
        name = f"USTB - {f.stem}"
        print(f"Creating query {name!r}...", flush=True)
        qid = create_query(name, sql)
        url = f"https://dune.com/queries/{qid}"
        created.append((f.name, qid))
        print(f"  -> id={qid}  {url}")
        if f.name.startswith("00_"):
            validation_query_id = qid

    if validation_query_id is None:
        print("No validation file (00_*.sql) found; skipping validation.")
    else:
        print()
        print("Executing validation scalars...")
        results = execute_and_wait(validation_query_id)
        rows = results.get("result", {}).get("rows", [])
        if not rows:
            print("  (no rows returned)")
        else:
            row = rows[0]
            supply = row.get("total_supply")
            holders = row.get("holder_count")
            print(f"  total_supply = {supply}")
            print(f"  holder_count = {holders}")
            if supply is not None and abs(supply - 65_300_000) / 65_300_000 > 0.25:
                print("  WARNING: total_supply is >25% off from 65.3M target")
            if holders is not None and abs(holders - 99) > 25:
                print("  WARNING: holder_count is >25 off from 99 target")

    print()
    print("Next step: open https://dune.com/browse/dashboards, create a new")
    print("dashboard, and add a visualization from each of these query IDs:")
    for name, qid in created:
        print(f"  {name:<45}  https://dune.com/queries/{qid}")


if __name__ == "__main__":
    main()

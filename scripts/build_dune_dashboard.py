#!/usr/bin/env python3
"""
Create/update, execute, and validate the USTB Dune queries via the Dune API.

Usage:
    export DUNE_API_KEY=...
    python scripts/build_dune_dashboard.py

Behavior:
  - Reads every SQL file in ../sql/.
  - Looks up persisted query IDs in ../.dune_query_ids.json.
  - For files without a saved ID, POSTs /query to create a saved query and
    records the new ID.
  - For files with a saved ID, PATCHes /query/{id} to update the SQL in place.
  - Executes the validation scalar query synchronously and prints
    total_supply / holder_count (targets: ~65.3M / ~99).
  - Writes the updated ID map back to ../.dune_query_ids.json.

Requires an Analyst-tier Dune key for query CRUD. The dashboard itself is not
created here — Dune's public API has no dashboard-creation endpoint. Open
https://dune.com/browse/dashboards and add one tile per query.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib import request, error

API_BASE = "https://api.dune.com/api/v1"
REPO_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = REPO_ROOT / "sql"
IDS_FILE = REPO_ROOT / ".dune_query_ids.json"


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


def load_ids() -> dict[str, int]:
    if not IDS_FILE.exists():
        return {}
    return json.loads(IDS_FILE.read_text())


def save_ids(ids: dict[str, int]) -> None:
    IDS_FILE.write_text(json.dumps(ids, indent=2, sort_keys=True) + "\n")


def create_query(name: str, sql: str) -> int:
    resp = call("POST", "/query", {
        "name": name,
        "query_sql": sql,
        "is_private": False,
    })
    return int(resp["query_id"])


def update_query(query_id: int, name: str, sql: str) -> None:
    call("PATCH", f"/query/{query_id}", {
        "name": name,
        "query_sql": sql,
    })


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

    ids = load_ids()
    validation_query_id: int | None = None

    for f in files:
        sql = f.read_text()
        name = f"USTB - {f.stem}"
        existing = ids.get(f.name)
        if existing is None:
            print(f"Creating query {name!r}...", flush=True)
            qid = create_query(name, sql)
            ids[f.name] = qid
            save_ids(ids)
        else:
            qid = existing
            print(f"Updating query {name!r} (id={qid})...", flush=True)
            update_query(qid, name, sql)
        print(f"  -> id={qid}  https://dune.com/queries/{qid}")
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
    print("dashboard, and add a visualization from each of these queries:")
    for name, qid in sorted(ids.items()):
        print(f"  {name:<45}  https://dune.com/queries/{qid}")


if __name__ == "__main__":
    main()

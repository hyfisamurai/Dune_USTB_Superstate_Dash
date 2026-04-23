# Repo context for agents

This repo builds a Dune monitoring dashboard for **USTB** (Superstate Short
Duration US Government Securities Fund), an ERC20 on Ethereum mainnet.

- Token contract: `0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e`
- Decimals: `6`
- Source table: `erc20_ethereum.evt_Transfer` (DuneSQL / Trino)

## Expected behavior when the user asks to "build the dashboard"

Pick the path that matches the tools you actually have available in the current
session. Do not guess — check first.

### Path A — Dune MCP is attached (preferred)

You'll see tools under `mcp__dune__*` (query CRUD, execution, dashboard
creation). In that case:

1. For each file in `sql/*.sql`, create (or update) a saved query named
   `USTB - <stem>`. Use the persisted ID map at `.dune_query_ids.json`
   when present — update in place rather than creating duplicates.
2. Execute `sql/00_validation_scalars.sql`. Confirm:
   - `total_supply` is in the neighborhood of **65,300,000**
   - `holder_count` is in the neighborhood of **99**
   If either is materially off (>25%), stop and surface the divergence
   before creating anything further.
3. Create a dashboard titled **USTB Monitoring — Superstate Short Duration**
   with one tile per non-validation query. Suggested layout:
   - Row 1: two counters from `00_validation_scalars` (supply, holders)
   - Row 2: area chart from `01_cumulative_supply` (wide)
   - Row 3: bar+line from `02_daily_transfer_volume` | line chart from
     `06_rolling_active_addresses`
   - Row 4: bar+line from `04_new_holders_and_cumulative` | table from
     `05_mint_burn_events`
   - Row 5: table from `03_top_20_holders` (wide, sorted by balance)
4. Persist any new/updated query IDs to `.dune_query_ids.json` and commit
   it (do not commit `DUNE_API_KEY`).
5. Return the dashboard URL to the user.

### Path B — No Dune MCP, but `DUNE_API_KEY` is set

Run `python3 scripts/build_dune_dashboard.py`. It creates/updates the 7
saved queries idempotently via the Dune REST API and runs the validation
scalar. Return the 7 query URLs and the supply/holder numbers. Dune's
REST API has no dashboard-creation endpoint, so explicitly tell the user
that dashboard assembly still needs either the MCP or the web UI — don't
pretend to have created a dashboard you didn't.

### Path C — Neither

Do nothing destructive. Explain the two options above to the user and
stop.

## Invariants to check before claiming success

- `01_cumulative_supply`'s final `cumulative_supply` == `00`'s
  `total_supply` (exact equality to 6 decimals).
- `04_new_holders_and_cumulative`'s final `cumulative_holders` ==
  `00`'s `holder_count`.
- Any single top-20 holder with `pct_of_supply` > 50 is suspicious;
  flag it.

## Hard rules

- Never commit a `DUNE_API_KEY`. `.mcp.json` uses `${DUNE_API_KEY}`
  expansion for a reason.
- Keep developing on `claude/ustb-dune-dashboard-qShLx` unless told
  otherwise.
- Do not create PRs unless the user explicitly asks.

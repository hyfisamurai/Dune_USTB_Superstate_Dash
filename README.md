# USTB Monitoring Dashboard — Dune

Monitoring dashboard scaffolding for **USTB** (Superstate Short Duration US
Government Securities Fund) on Ethereum mainnet.

- Token contract: `0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e`
- Decimals: `6`
- Source table: `erc20_ethereum.evt_Transfer` (DuneSQL / Trino)

## Status

The SQL in `sql/` is ready to paste into Dune. This repo does **not**
execute the queries or create the dashboard automatically — the environment
that generated these files did not have a Dune MCP server attached, so the
`~65.3M supply` / `~99 holder` validation and dashboard creation need to be
done manually (or rerun with Dune MCP available).

## Queries

| # | File | Panel | Suggested viz |
|---|------|-------|---------------|
| 0 | `sql/00_validation_scalars.sql` | Sanity check: current supply + holder count | 2 × Counter |
| 1 | `sql/01_cumulative_supply.sql` | Cumulative supply over time (AUM proxy) | Area chart on `cumulative_supply` |
| 2 | `sql/02_daily_transfer_volume.sql` | Daily transfer volume + count (excl. mints/burns) | Bar chart (volume) + line (count) on dual axis |
| 3 | `sql/03_top_20_holders.sql` | Top 20 holders with % of supply | Table, sorted by `balance` desc |
| 4 | `sql/04_new_holders_and_cumulative.sql` | New holders per day + cumulative | Bar (`new_holders`) + line (`cumulative_holders`) |
| 5 | `sql/05_mint_burn_events.sql` | Mint/burn events log | Table |
| 6 | `sql/06_rolling_active_addresses.sql` | Rolling 7D / 30D active addresses | Line chart, two series |

## Setup

### Option A — automated (requires Dune Plus for saved-query API)

Either run locally:

```
export DUNE_API_KEY=...
python3 scripts/build_dune_dashboard.py
```

Or trigger the **Build USTB Dune queries** workflow from the Actions tab
(requires a `DUNE_API_KEY` repository secret). It also runs on push when
`sql/` or the builder changes. Both paths run the same script.

The script is idempotent: the first run creates 7 saved queries and
writes their IDs to `.dune_query_ids.json`; subsequent runs PATCH the
same queries in place, so re-running never creates duplicates in your
Dune account.

The script creates all 7 queries in your Dune account, executes
`00_validation_scalars.sql`, prints the supply/holder numbers, and lists
the query IDs. Dashboard assembly is still manual (Dune has no public
dashboard-creation endpoint): open <https://dune.com/browse/dashboards>,
click **New dashboard**, and add a visualization from each query.

### Option B — fully manual

1. Go to <https://dune.com/queries> and create a new query for each file
   in `sql/`. Paste the SQL, name the query (e.g. `USTB — Cumulative Supply`),
   run, and save.
2. Add a visualization to each saved query per the table above.
3. Run `00_validation_scalars.sql` and confirm:
   - `total_supply` is in the neighborhood of **65.3M**
   - `holder_count` is in the neighborhood of **99**
   If either number is materially off, re-check the contract address and that
   `erc20_ethereum.evt_Transfer` is decoding this token (it's a standard ERC20
   so it should be).
4. Create a new dashboard, add each visualization as a tile, and arrange:
   - Row 1: validation counters (supply, holder count)
   - Row 2: cumulative supply (wide)
   - Row 3: daily volume/count + rolling active addresses
   - Row 4: new holders chart + mint/burn log
   - Row 5: top 20 holders table (full width)
5. Publish the dashboard and record its URL below.

## Notes on query design

- Mints are identified as transfers from the zero address; burns as transfers
  to the zero address. Superstate issues and destroys shares via zero-address
  transfers, so panel 5 maps directly onto subscriptions/redemptions.
- Balances are reconstructed by summing all `Transfer` deltas per address.
  This is exact for standard ERC20s with no rebasing logic.
- Panel 4 defines a "holder" as an address with positive current balance and
  attributes each current holder to the day of their first-ever receive.
  This makes the final `cumulative_holders` value equal the current holder
  count (target ~99) rather than an ever-held count, which would drift higher.
- All `value` casts go through `DOUBLE`. For a 6-decimal token at ~$1 per share
  this does not hit float-precision limits; if USTB ever reaches tens of
  trillions of base units, switch to `DECIMAL(38, 0)`.

-- Panel 4: New holders per day and cumulative current-holder count
-- "Current holder" = address with positive balance right now.
-- Each current holder is attributed to the day they first received USTB.
-- Final cumulative value should equal the current holder count (~99).

WITH flows AS (
  SELECT
    "to"  AS address,
     CAST(value AS DOUBLE)                 AS delta,
     date_trunc('day', evt_block_time)     AS received_day
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
  UNION ALL
  SELECT
    "from" AS address,
    -CAST(value AS DOUBLE) AS delta,
    NULL                   AS received_day
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
),
per_address AS (
  SELECT
    address,
    SUM(delta) / 1e6     AS balance,
    MIN(received_day)    AS first_received_day
  FROM flows
  WHERE address != 0x0000000000000000000000000000000000000000
  GROUP BY address
),
current_holders AS (
  SELECT first_received_day AS day
  FROM per_address
  WHERE balance > 0
),
daily AS (
  SELECT day, COUNT(*) AS new_holders
  FROM current_holders
  GROUP BY day
)
SELECT
  day,
  new_holders,
  SUM(new_holders) OVER (ORDER BY day) AS cumulative_holders
FROM daily
ORDER BY day;

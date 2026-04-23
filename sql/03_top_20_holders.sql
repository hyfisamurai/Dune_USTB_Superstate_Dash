-- Panel 3: Top 20 holders with % of supply
-- Balance reconstructed from cumulative transfers.

WITH flows AS (
  SELECT "to"   AS address,  CAST(value AS DOUBLE) AS delta
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
  UNION ALL
  SELECT "from" AS address, -CAST(value AS DOUBLE) AS delta
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
),
balances AS (
  SELECT address, SUM(delta) / 1e6 AS balance
  FROM flows
  WHERE address != 0x0000000000000000000000000000000000000000
  GROUP BY address
  HAVING SUM(delta) > 0
),
total AS (
  SELECT SUM(balance) AS total_supply FROM balances
)
SELECT
  b.address,
  b.balance,
  b.balance / t.total_supply * 100 AS pct_of_supply
FROM balances b
CROSS JOIN total t
ORDER BY b.balance DESC
LIMIT 20;

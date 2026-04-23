-- Validation scalars — run first to sanity-check the data.
-- Expected: total_supply ~ 65,300,000   holder_count ~ 99

WITH flows AS (
  SELECT "to"  AS address,  CAST(value AS DOUBLE) AS delta
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
)
SELECT
  SUM(CASE WHEN balance > 0 THEN balance END) AS total_supply,
  COUNT(CASE WHEN balance > 0 THEN 1 END)     AS holder_count
FROM balances;

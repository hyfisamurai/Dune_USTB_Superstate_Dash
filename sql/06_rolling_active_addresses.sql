-- Panel 6: Rolling 7D and 30D active addresses
-- An address is "active" on day D if it appeared as sender or receiver
-- of a non-zero-address transfer on day D. The 7D/30D windows are
-- trailing (inclusive of the reported day).

WITH activity AS (
  SELECT date_trunc('day', evt_block_time) AS day, "from" AS address
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
    AND "from" != 0x0000000000000000000000000000000000000000
  UNION
  SELECT date_trunc('day', evt_block_time) AS day, "to" AS address
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
    AND "to" != 0x0000000000000000000000000000000000000000
),
days AS (
  SELECT DISTINCT day FROM activity
)
SELECT
  d.day,
  COUNT(DISTINCT CASE
    WHEN a.day BETWEEN d.day - INTERVAL '6'  DAY AND d.day THEN a.address
  END) AS active_7d,
  COUNT(DISTINCT CASE
    WHEN a.day BETWEEN d.day - INTERVAL '29' DAY AND d.day THEN a.address
  END) AS active_30d
FROM days d
JOIN activity a
  ON a.day BETWEEN d.day - INTERVAL '29' DAY AND d.day
GROUP BY d.day
ORDER BY d.day;

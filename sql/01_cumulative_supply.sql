-- Panel 1: Cumulative USTB supply over time (AUM proxy)
-- Net daily mints minus burns, running total.
-- Expected final value: ~65.3M USTB.

WITH daily_net AS (
  SELECT
    date_trunc('day', evt_block_time) AS day,
    SUM(
      CASE
        WHEN "from" = 0x0000000000000000000000000000000000000000 THEN  CAST(value AS DOUBLE)
        WHEN "to"   = 0x0000000000000000000000000000000000000000 THEN -CAST(value AS DOUBLE)
        ELSE 0
      END
    ) / 1e6 AS net_change
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
    AND (
         "from" = 0x0000000000000000000000000000000000000000
      OR "to"   = 0x0000000000000000000000000000000000000000
    )
  GROUP BY 1
)
SELECT
  day,
  net_change,
  SUM(net_change) OVER (ORDER BY day) AS cumulative_supply
FROM daily_net
ORDER BY day;

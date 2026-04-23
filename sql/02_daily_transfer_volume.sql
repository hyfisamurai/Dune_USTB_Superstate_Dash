-- Panel 2: Daily transfer volume and count (secondary activity)
-- Excludes mints (from = 0x0) and burns (to = 0x0).

SELECT
  date_trunc('day', evt_block_time) AS day,
  COUNT(*)                          AS transfer_count,
  SUM(CAST(value AS DOUBLE)) / 1e6  AS transfer_volume
FROM erc20_ethereum.evt_Transfer
WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
  AND "from" != 0x0000000000000000000000000000000000000000
  AND "to"   != 0x0000000000000000000000000000000000000000
GROUP BY 1
ORDER BY 1;

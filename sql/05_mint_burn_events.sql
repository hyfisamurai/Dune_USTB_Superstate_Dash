-- Panel 5: Mint / burn events log (subscriptions & redemptions)
-- Mint  = Transfer from 0x0 (subscription: Superstate issues shares)
-- Burn  = Transfer to   0x0 (redemption: Superstate destroys shares)

SELECT
  evt_block_time AS block_time,
  CASE
    WHEN "from" = 0x0000000000000000000000000000000000000000 THEN 'mint'
    WHEN "to"   = 0x0000000000000000000000000000000000000000 THEN 'burn'
  END AS event_type,
  CASE
    WHEN "from" = 0x0000000000000000000000000000000000000000 THEN "to"
    WHEN "to"   = 0x0000000000000000000000000000000000000000 THEN "from"
  END                              AS counterparty,
  CAST(value AS DOUBLE) / 1e6      AS amount,
  evt_tx_hash                      AS tx_hash
FROM erc20_ethereum.evt_Transfer
WHERE contract_address = 0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e
  AND (
       "from" = 0x0000000000000000000000000000000000000000
    OR "to"   = 0x0000000000000000000000000000000000000000
  )
ORDER BY block_time DESC;

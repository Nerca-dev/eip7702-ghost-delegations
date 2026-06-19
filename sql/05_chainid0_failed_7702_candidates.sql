select
    tx.block_time,
    tx.block_number,
    tx."index" as tx_index,
    tx.hash as tx_hash,
    tx."from" as tx_sender,
    tx."to" as tx_to,
    tx.gas_used,
    cardinality(tx.authorization_list) as tx_auth_count,

    auth_chain_id,
    delegate_address,
    auth_nonce,
    auth_r,
    auth_s,
    y_parity

from ethereum.transactions tx
cross join unnest(tx.authorization_list) as u(
    auth_chain_id,
    delegate_address,
    auth_nonce,
    auth_r,
    auth_s,
    y_parity
)
where tx.block_time >= now() - interval '30' day
  and tx.success = false
  and tx.type = 'EIP-7702'
  and auth_chain_id = 0
order by tx.block_number desc, tx."index" desc
limit 100;

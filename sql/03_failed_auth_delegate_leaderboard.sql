with failed_auths as (
    select
        tx.block_time,
        tx.block_number,
        tx."index" as tx_index,
        tx.hash as tx_hash,
        tx."from" as tx_sender,

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
      and tx.authorization_list is not null
      and cardinality(tx.authorization_list) > 0
)

select
    delegate_address,
    count(*) as failed_auth_tuples,
    count(distinct tx_hash) as failed_txs,
    count(distinct tx_sender) as unique_tx_senders,
    count_if(auth_chain_id = 0) as chain_id_0_auths,
    min(block_time) as first_seen,
    max(block_time) as last_seen
from failed_auths
group by 1
order by failed_auth_tuples desc
limit 50;

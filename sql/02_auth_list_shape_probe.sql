-- Dune output order observed:
-- chain_id, address, nonce, r, s, y_parity

with candidates as (
    select
        block_time,
        block_number,
        "index" as tx_index,
        hash as tx_hash,
        "from" as tx_sender,
        success,
        authorization_list
    from ethereum.transactions
    where block_time >= now() - interval '30' day
      and success = false
      and authorization_list is not null
      and cardinality(authorization_list) > 0
    order by block_number desc, tx_index desc
    limit 20
)

select
    block_time,
    block_number,
    tx_index,
    tx_hash,
    tx_sender,
    success,

    auth_chain_id,
    delegate_address,
    auth_nonce,
    auth_r,
    auth_s,
    y_parity

from candidates
cross join unnest(authorization_list) as u(
    auth_chain_id,
    delegate_address,
    auth_nonce,
    auth_r,
    auth_s,
    y_parity
);

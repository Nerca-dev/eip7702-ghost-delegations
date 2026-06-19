-- Export/paste this into JSONL or CSV for the verifier.
-- Labels are candidate-only, not proof.

with failed_7702 as (
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
      and tx.authorization_list is not null
      and cardinality(tx.authorization_list) > 0
)

select
    block_time,
    block_number,
    tx_index,
    tx_hash,
    tx_sender,
    tx_to,
    gas_used,
    tx_auth_count,

    auth_chain_id,
    delegate_address,
    auth_nonce,
    auth_r,
    auth_s,
    y_parity,

    case
        when auth_chain_id = 0 then 'chain_id_0'
        when tx_auth_count >= 10 then 'multi_auth_failed_tx'
        else 'standard_candidate'
    end as candidate_reason

from failed_7702
order by
    case when auth_chain_id = 0 then 0 else 1 end,
    tx_auth_count desc,
    block_number desc,
    tx_index desc
limit 5000;

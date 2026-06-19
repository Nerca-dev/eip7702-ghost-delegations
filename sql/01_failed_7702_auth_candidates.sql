-- Candidate finder only.
-- A row here means:
-- tx failed + it carried at least one EIP-7702 authorization tuple.
-- It does NOT prove a ghost delegation yet.

select
    block_time,
    block_number,
    "index" as tx_index,
    hash as tx_hash,
    "from" as tx_sender,
    "to" as tx_to,
    success,
    type,
    gas_used,
    cardinality(authorization_list) as auth_count,
    authorization_list
from ethereum.transactions
where block_time >= now() - interval '30' day
  and success = false
  and authorization_list is not null
  and cardinality(authorization_list) > 0
order by block_number desc, tx_index desc
limit 100;

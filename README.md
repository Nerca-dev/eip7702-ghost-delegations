# 7702 Ghost Delegations

Failed transaction does not mean failed delegation.

This repo verifies a narrow EIP-7702 behavior: a transaction can fail at the receipt/execution level while processed authorization-list delegation state remains changed.

This is not a zero-day claim. It is a forensic monitor for documented protocol behavior and an observability gap.

## Why This Exists

Most users read a failed transaction as "nothing happened." With EIP-7702, that assumption can be wrong. Authorization processing happens before execution, and processed delegation designations are not rolled back by later execution failure.

## What This Repo Does

1. Uses Dune SQL to find candidate failed EIP-7702 transactions with non-empty authorization lists.
2. Recovers the affected authority from the auth signature.
3. Validates the tuple.
4. Checks historical account code before and after the failed transaction.
5. Classifies whether the delegation is active, cleared, replaced, already present, invalid, or ambiguous.

The authorization tuple address is the delegate/code address, not the affected wallet. The verifier recovers the affected authority from:

```text
keccak(0x05 || rlp([chain_id, delegate_address, nonce]))
```

A valid processed authorization sets the authority's code to:

```text
0xef0100 || delegate_address
```

## What This Repo Does Not Do

- It does not label every failed 7702 auth as a ghost.
- It does not claim maliciousness from delegation alone.
- It does not treat nonce movement as revocation.
- It does not rely on current `eth_getCode` alone.
- It does not publish drain-style PoCs.

## Usage

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export RPC_URL="https://your-archive-ethereum-rpc"
python src/verify_ghost.py data/sample_candidates.jsonl --out data/verified.jsonl
cat data/verified.jsonl
```

The RPC must support archive reads for historical `eth_getCode` and `eth_getTransactionCount`.

If `eth-utils` reports that no `eth-hash` backend is installed, add one inside your environment:

```bash
pip install "eth-hash[pycryptodome]"
```

## Labels

- `invalid_auth`: basic tuple validation failed, or the authority signature could not be recovered.
- `not_delegated_after_block`: the authority was not delegated at the end of the candidate block.
- `already_delegated_before_still_active`: the authority was already delegated to the same delegate before the failed transaction block and remains delegated to it.
- `already_delegated_before_changed_later`: the authority was already delegated to the same delegate before the failed transaction block but no longer has that same current delegation.
- `active_ghost`: pre-block code was not delegated to the expected delegate, post-block code was delegated to the expected delegate, and latest state is still delegated to it.
- `cleared_ghost`: pre/post state indicates the failed transaction block introduced the expected delegation, but latest state no longer has an EIP-7702 delegation designator.
- `replaced_ghost`: pre/post state indicates the failed transaction block introduced the expected delegation, but latest state points at a different delegate.
- `post_delegated_to_different_delegate`: post-block state is delegated, but not to the delegate from the candidate tuple.
- `nonce_mismatch_or_same_block_ambiguous`: nonce evidence does not support attributing the block-level code transition to this exact candidate transaction.
- `rpc_failed`: the verifier could not fetch required state from the RPC.

## Proof Levels

- `candidate_only`: Dune row only.
- `candidate_checked`: verifier ran but did not prove a ghost transition.
- `archive_state_confirmed`: pre/post/current state was checked with archive RPC.

Archive state is still block-level state. When nonce evidence suggests another same-block action may have affected the same authority, the verifier uses `nonce_mismatch_or_same_block_ambiguous` rather than claiming exact transaction causality.

## Case Study Format

Failed receipt + valid auth + recovered authority + pre-code not delegated/different + post-code delegated + current state classified.

Use [case-study/failed-transaction-active-delegation.md](case-study/failed-transaction-active-delegation.md) as the template.

## Dune Workflow

Start with [sql/01_failed_7702_auth_candidates.sql](sql/01_failed_7702_auth_candidates.sql) to find failed transactions carrying authorization lists. Use [sql/02_auth_list_shape_probe.sql](sql/02_auth_list_shape_probe.sql) when validating Dune's unnest shape, then export verifier rows with [sql/04_export_failed_7702_auth_candidates.sql](sql/04_export_failed_7702_auth_candidates.sql).

## Foundry PoC

The [poc/](poc) directory is intentionally harmless. It contains a delegate with a `ping()` behavior change and a target that reverts. The test file is a scaffold because direct EIP-7702 transaction construction may require Foundry support, a cheatcode, or custom fork tooling depending on the installed version.

## Disclaimer

This is research tooling. Labels are heuristics/evidence states, not accusations.

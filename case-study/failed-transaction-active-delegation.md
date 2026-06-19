# Failed Transaction, Active Delegation

## Summary

Failed transaction does not mean failed delegation.

This case study documents one EIP-7702 transaction with a failed receipt where the authorization evidence and archive-state checks show the authority account became delegated across the failed transaction's block and remained delegated at latest check.

A failed EIP-7702 transaction can still leave an account delegated. In this case, archive-state checks show an authority account had empty code before the failed transaction's block, then had `0xef0100 || delegate` code after that block, and still had the same delegation at latest check.

This is a single verified case-study candidate, not a claim about scale. Dune rows are only candidates; the verifier produced the evidence packet below.

## Evidence packet

| Field | Value |
|---|---|
| Transaction | `0xa420045ee252defae20170543bcaa9ced04254d91bd81c588044d393665742f6` |
| Block | `25289575` |
| Tx index | `121` |
| Receipt status | `failed` |
| Auth chain ID | `0` |
| Authority | `0x644D8E9b78437b6cD80c673C600cfE2258F2900B` |
| Delegate | `0x00000000383e8cbe298514674ea60ee1d1de50ac` |
| Pre-code at block 25289574 | `0x` |
| Post-code at block 25289575 | `0xef0100...50ac` |
| Current code | `0xef0100...50ac` |
| Pre nonce | `0` |
| Post nonce | `1` |
| Current nonce | `1` |
| State | `active_ghost` |
| Proof level | `archive_state_confirmed` |

## What was verified

- The receipt status was failed.
- The authorization tuple used chain ID `0`.
- The authority was recovered from the EIP-7702 authorization signature.
- The signature recovered successfully.
- The chain ID rule passed.
- The low-s check passed.
- The nonce bound check passed.
- The pre-block nonce matched the authorization nonce.
- The pre-block account code was empty.
- The post-block account code was `0xef0100 || delegate`.
- The latest account code still matched the same delegation.
- The verifier recorded the latest block number used for the current-state check as `current_checked_block` in `data/verified.jsonl`.

## Why this matters

Most users and dashboards treat a failed transaction as "nothing happened." EIP-7702 makes that mental model incomplete. Authorization processing can change account delegation state even when later execution fails. Wallets, explorers, and monitoring systems should surface delegation state separately from transaction success.

## Limitations

This is not an accusation of malicious behavior. This case study does not claim asset loss or exploitability. It demonstrates a protocol-level observability gap.

The evidence is archive block-boundary evidence. It shows the authority account changed from empty code before the block to EIP-7702 delegation code after the block. It does not claim transaction-index trace proof excluding every possible earlier same-block state transition.

## Reproduction

Run the verifier against the included sample candidates with an archive-capable Ethereum RPC:

```bash
source .venv/bin/activate
python src/verify_ghost.py data/sample_candidates.jsonl --out data/verified.jsonl
grep active_ghost data/verified.jsonl
```

## Conclusion

Failed transaction status is not enough to reason about EIP-7702 wallet state.

#!/usr/bin/env python3
import argparse
import json
import os
import sys

from classify import (
    INVALID_AUTH,
    NONCE_MISMATCH_OR_SAME_BLOCK_AMBIGUOUS,
    RPC_FAILED,
    classify_code_transition,
)
from eip7702_auth import (
    hx_to_int,
    is_chain_id_valid,
    is_low_s,
    is_nonce_valid,
    parse_delegate_from_code,
    recover_authority,
)
from rpc_state import RPCError, get_code, get_nonce


GHOST_STATES = {"active_ghost", "cleared_ghost", "replaced_ghost"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify failed EIP-7702 authorization-list candidates against archive state."
    )
    parser.add_argument("input", help="JSONL file exported from Dune")
    parser.add_argument("--rpc", default=os.environ.get("RPC_URL"), help="Ethereum archive RPC URL")
    parser.add_argument(
        "--chain-id",
        type=int,
        default=int(os.environ.get("CHAIN_ID", "1")),
        help="current chain id; auth chain id 0 is treated as valid wildcard",
    )
    parser.add_argument("--out", default="data/verified.jsonl", help="output JSONL evidence path")
    return parser.parse_args()


def bool_from_row(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "success"}
    return bool(value)


def blank_state_fields():
    return {
        "pre_code": None,
        "post_code": None,
        "current_code": None,
        "pre_delegate": None,
        "post_delegate": None,
        "current_delegate": None,
        "pre_nonce": None,
        "post_nonce": None,
        "current_nonce": None,
        "nonce_matches_pre_block": None,
        "post_nonce_expected_increment": None,
    }


def base_packet(row, chain_id):
    auth_chain_id = hx_to_int(row["auth_chain_id"])
    auth_nonce = hx_to_int(row["auth_nonce"])
    delegate = row["delegate_address"]
    s = hx_to_int(row["auth_s"])

    packet = {
        "tx_hash": row.get("tx_hash") or row.get("hash"),
        "block_number": hx_to_int(row["block_number"]),
        "tx_index": hx_to_int(row.get("tx_index", row.get("index", 0))),
        "receipt_status": bool_from_row(row.get("success"), default=False),
        "auth_chain_id": auth_chain_id,
        "delegate": delegate,
        "auth_nonce": auth_nonce,
        "authority": None,
        "chain_id_valid": is_chain_id_valid(auth_chain_id, chain_id),
        "low_s_valid": is_low_s(s),
        "nonce_bound_valid": is_nonce_valid(auth_nonce),
        "signature_recovered": False,
        "pre_block": hx_to_int(row["block_number"]) - 1,
        "post_block": hx_to_int(row["block_number"]),
        "state": None,
        "proof_level": "candidate_checked",
    }
    packet.update(blank_state_fields())
    return packet


def verify_row(row, rpc_url, chain_id):
    packet = base_packet(row, chain_id)

    try:
        packet["authority"] = recover_authority(row)
        packet["signature_recovered"] = True
    except Exception as exc:
        packet["recovery_error"] = str(exc)

    basic_valid = (
        packet["chain_id_valid"]
        and packet["low_s_valid"]
        and packet["nonce_bound_valid"]
        and packet["signature_recovered"]
    )
    if not basic_valid:
        packet["state"] = INVALID_AUTH
        return packet

    try:
        packet["pre_code"] = get_code(rpc_url, packet["authority"], packet["pre_block"])
        packet["post_code"] = get_code(rpc_url, packet["authority"], packet["post_block"])
        packet["current_code"] = get_code(rpc_url, packet["authority"], "latest")
        packet["pre_nonce"] = get_nonce(rpc_url, packet["authority"], packet["pre_block"])
        packet["post_nonce"] = get_nonce(rpc_url, packet["authority"], packet["post_block"])
        packet["current_nonce"] = get_nonce(rpc_url, packet["authority"], "latest")
    except RPCError as exc:
        packet["state"] = RPC_FAILED
        packet["rpc_error"] = str(exc)
        return packet

    packet["pre_delegate"] = parse_delegate_from_code(packet["pre_code"])
    packet["post_delegate"] = parse_delegate_from_code(packet["post_code"])
    packet["current_delegate"] = parse_delegate_from_code(packet["current_code"])
    packet["nonce_matches_pre_block"] = packet["pre_nonce"] == packet["auth_nonce"]
    packet["post_nonce_expected_increment"] = packet["post_nonce"] == packet["auth_nonce"] + 1

    if not packet["nonce_matches_pre_block"]:
        packet["state"] = NONCE_MISMATCH_OR_SAME_BLOCK_AMBIGUOUS
        packet["proof_level"] = "archive_state_confirmed"
        return packet

    packet["state"] = classify_code_transition(
        packet["pre_code"],
        packet["post_code"],
        packet["current_code"],
        packet["delegate"],
    )
    packet["proof_level"] = "archive_state_confirmed"
    return packet


def iter_jsonl(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc


def main():
    args = parse_args()
    if not args.rpc:
        print("RPC URL required via --rpc or RPC_URL", file=sys.stderr)
        return 2

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as output:
        for row in iter_jsonl(args.input):
            packet = verify_row(row, args.rpc, args.chain_id)
            output.write(json.dumps(packet, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import requests


class RPCError(RuntimeError):
    pass


def block_to_hex(block):
    if block is None:
        return "latest"
    if isinstance(block, str):
        if block in {"latest", "earliest", "pending", "safe", "finalized"}:
            return block
        if block.startswith(("0x", "0X")):
            return block
        block = int(block, 10)
    block_int = int(block)
    if block_int < 0:
        raise ValueError("block number cannot be negative")
    return hex(block_int)


def rpc_call(rpc_url, method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise RPCError(f"request failed for {method}: {exc}") from exc
    except ValueError as exc:
        raise RPCError(f"invalid JSON-RPC response for {method}") from exc

    if "error" in data:
        raise RPCError(f"RPC error for {method}: {data['error']}")
    if "result" not in data:
        raise RPCError(f"missing result for {method}")
    return data["result"]


def get_code(rpc_url, address, block):
    return rpc_call(rpc_url, "eth_getCode", [address, block_to_hex(block)])


def get_nonce(rpc_url, address, block):
    result = rpc_call(rpc_url, "eth_getTransactionCount", [address, block_to_hex(block)])
    return int(result, 16)

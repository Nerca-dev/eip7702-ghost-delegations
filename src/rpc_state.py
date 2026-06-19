import requests


class RPCError(RuntimeError):
    pass


def hex_to_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.startswith(("0x", "0X")) else int(value, 10)
    return int(value)


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


def rpc_call(rpc_url, method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
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


def get_block_number(rpc_url):
    return hex_to_int(rpc_call(rpc_url, "eth_blockNumber"))


def get_transaction_receipt(rpc_url, tx_hash):
    receipt = rpc_call(rpc_url, "eth_getTransactionReceipt", [tx_hash])
    if receipt is None:
        raise RPCError(f"transaction receipt not found for {tx_hash}")
    return receipt


def get_code(rpc_url, address, block):
    return rpc_call(rpc_url, "eth_getCode", [address, block_to_hex(block)])


def get_nonce(rpc_url, address, block):
    result = rpc_call(rpc_url, "eth_getTransactionCount", [address, block_to_hex(block)])
    return hex_to_int(result)

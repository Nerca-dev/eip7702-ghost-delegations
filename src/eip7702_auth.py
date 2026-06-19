from eth_keys import keys
from eth_utils import keccak, to_checksum_address
import rlp


SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1_HALF_N = SECP256K1_N // 2
MAX_AUTH_NONCE_EXCLUSIVE = 2**64 - 1
DELEGATION_PREFIX = "0xef0100"


def hx_to_int(value):
    if isinstance(value, int):
        return value
    if isinstance(value, bytes):
        return int.from_bytes(value, "big")
    if isinstance(value, str):
        value = value.strip()
        if value.startswith(("0x", "0X")):
            if value in ("0x", "0X"):
                return 0
            return int(value, 16)
        return int(value, 10)
    raise TypeError(f"cannot convert {type(value).__name__} to int")


def _normalize_address(address):
    if not isinstance(address, str):
        raise TypeError("address must be a hex string")
    body = address[2:] if address.startswith(("0x", "0X")) else address
    if len(body) != 40:
        raise ValueError(f"address must be 20 bytes, got {len(body) // 2} bytes")
    int(body, 16)
    return "0x" + body.lower()


def _address_bytes(address):
    return bytes.fromhex(_normalize_address(address)[2:])


def recover_authority(row):
    chain_id = hx_to_int(row["auth_chain_id"])
    delegate_bytes = _address_bytes(row["delegate_address"])
    nonce = hx_to_int(row["auth_nonce"])
    y_parity = hx_to_int(row["y_parity"])
    r = hx_to_int(row["auth_r"])
    s = hx_to_int(row["auth_s"])

    msg_hash = keccak(b"\x05" + rlp.encode([chain_id, delegate_bytes, nonce]))
    sig = keys.Signature(vrs=(y_parity, r, s))
    authority = sig.recover_public_key_from_msg_hash(msg_hash).to_checksum_address()
    return authority


def is_low_s(s):
    s_int = hx_to_int(s)
    return 1 <= s_int <= SECP256K1_HALF_N


def is_chain_id_valid(auth_chain_id, current_chain_id):
    chain_id = hx_to_int(auth_chain_id)
    return chain_id == 0 or chain_id == hx_to_int(current_chain_id)


def is_nonce_valid(nonce):
    nonce_int = hx_to_int(nonce)
    return 0 <= nonce_int < MAX_AUTH_NONCE_EXCLUSIVE


def delegation_code_for(delegate):
    return DELEGATION_PREFIX + _normalize_address(delegate)[2:]


def parse_delegate_from_code(code):
    if not isinstance(code, str):
        return None
    code = code.strip().lower()
    if not code.startswith("0x"):
        code = "0x" + code
    expected_len = len(DELEGATION_PREFIX) + 40
    if len(code) != expected_len or not code.startswith(DELEGATION_PREFIX):
        return None
    delegate = "0x" + code[len(DELEGATION_PREFIX):]
    return to_checksum_address(delegate)

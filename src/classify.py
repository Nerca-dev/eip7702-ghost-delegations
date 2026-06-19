from eip7702_auth import parse_delegate_from_code


INVALID_AUTH = "invalid_auth"
NOT_DELEGATED_AFTER_BLOCK = "not_delegated_after_block"
ALREADY_DELEGATED_BEFORE_STILL_ACTIVE = "already_delegated_before_still_active"
ALREADY_DELEGATED_BEFORE_CHANGED_LATER = "already_delegated_before_changed_later"
ACTIVE_GHOST = "active_ghost"
CLEARED_GHOST = "cleared_ghost"
REPLACED_GHOST = "replaced_ghost"
POST_DELEGATED_TO_DIFFERENT_DELEGATE = "post_delegated_to_different_delegate"
NONCE_MISMATCH_OR_SAME_BLOCK_AMBIGUOUS = "nonce_mismatch_or_same_block_ambiguous"
SENDER_AUTHORITY_NONCE_EDGE = "sender_authority_nonce_edge"
RPC_FAILED = "rpc_failed"


def _same_address(left, right):
    if left is None or right is None:
        return False
    return left.lower() == right.lower()


def classify_code_transition(pre_code, post_code, current_code, expected_delegate):
    pre_delegate = parse_delegate_from_code(pre_code)
    post_delegate = parse_delegate_from_code(post_code)
    current_delegate = parse_delegate_from_code(current_code)

    if post_delegate is None:
        return NOT_DELEGATED_AFTER_BLOCK

    if not _same_address(post_delegate, expected_delegate):
        return POST_DELEGATED_TO_DIFFERENT_DELEGATE

    if _same_address(pre_delegate, expected_delegate):
        if _same_address(current_delegate, expected_delegate):
            return ALREADY_DELEGATED_BEFORE_STILL_ACTIVE
        return ALREADY_DELEGATED_BEFORE_CHANGED_LATER

    if _same_address(current_delegate, expected_delegate):
        return ACTIVE_GHOST

    if current_delegate is None:
        return CLEARED_GHOST

    return REPLACED_GHOST

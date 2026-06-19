// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {HarmlessDelegate} from "../src/HarmlessDelegate.sol";
import {Reverter} from "../src/Reverter.sol";

// Scaffold only.
//
// This file documents the intended harmless EIP-7702 reproduction flow. It does
// not pretend to be a passing test because direct 7702 transaction construction
// may require Foundry support, a cheatcode, or custom fork tooling depending on
// the installed Foundry version.
//
// Test idea:
// 1. An EOA signs a 7702 authorization.
// 2. Transaction execution calls a target that reverts.
// 3. The authorization processing happens before execution.
// 4. Even though execution reverts, account code can remain 0xef0100 || delegate.
// 5. A later call observes delegated behavior through HarmlessDelegate.ping().
//
// The delegate is intentionally harmless: it emits an event and returns a fixed
// hash. There is no mainnet victim path and no asset movement behavior.
abstract contract FailedTxStillDelegatesScaffold {
    HarmlessDelegate internal delegate;
    Reverter internal reverter;

    function _deployScaffoldContracts() internal {
        delegate = new HarmlessDelegate();
        reverter = new Reverter();
    }

    function _expectedDelegationCode(address delegateAddress) internal pure returns (bytes memory) {
        return abi.encodePacked(hex"ef0100", delegateAddress);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Reverter {
    function alwaysRevert() external pure {
        revert("execution failed after auth processing");
    }
}

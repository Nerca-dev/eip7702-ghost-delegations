// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract HarmlessDelegate {
    event Ping(address caller, address context);

    function ping() external returns (bytes32) {
        emit Ping(msg.sender, address(this));
        return keccak256("delegated-behavior-active");
    }
}

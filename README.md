# Withdrawals Manager contract stub

Though the Beacon chain already supports setting withdrawal credentials pointing to a smart
contract, the withdrawals specification is not yet final and might change before withdrawals
are enabled in the Merge network. This means that Lido cannot deploy the final implementation
of the withdrawals manager contract yet. At the same time, it's desirable to have withdrawal
credentials pointing to a smart contract since this would avoid the need to migrate a lot of
validators to new withdrawal credentials once withdrawals are enabled.

To solve this, Lido uses a DAO-controlled upgradeable proxy, [`WithdrawalsManagerProxy`].
Initially, the proxy uses a stub implementation contract, [`WithdrawalsManagerStub`], that cannot
receive Ether. The implementation can only be changed by LDO holders collectively by performing a
DAO vote. Lido DAO will vote for setting validator withdrawal credentials pointing to this proxy
contract.

When Ethereum 2.0 withdrawals specification is finalized, Lido DAO will prepare the new
implementation contract and initiate a vote among LDO holders for upgrading this proxy to the
new implementation.

Once withdrawals are enabled in Ethereum 2.0, Lido DAO members will start a vote among LDO
holders for disabling the upgradeability forever and locking the implementation by changing
proxy admin from the DAO Voting contract to a zero address (which is an irreversible action).

[`WithdrawalsManagerStub`]: ./contracts/WithdrawalsManagerStub.sol
[`WithdrawalsManagerProxy`]: ./contracts/WithdrawalsManagerProxy.sol


## Audits

This contract [was audited by MixBytes] in May, 2021.

[was audited by MixBytes]: https://github.com/lidofinance/audits#05-2021-mixbytes-audit-withdrawals-manager-proxy-and-stub

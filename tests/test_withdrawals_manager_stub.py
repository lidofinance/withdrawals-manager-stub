import pytest
from brownie import ZERO_ADDRESS, Contract, reverts


@pytest.fixture(scope='function')
def withdrawals_proxy(deployer, WithdrawalsManagerProxy):
    return WithdrawalsManagerProxy.deploy({'from': deployer})


@pytest.fixture(scope='function')
def new_impl(deployer, Test__NewImplementation):
    return Test__NewImplementation.deploy({'from': deployer})


def test_cannot_receive_ether_by_plain_call(withdrawals_proxy, stranger):
    with reverts('not supported'):
        stranger.transfer(withdrawals_proxy, '0.1 ether')


def test_cannot_receive_ether_by_call_with_data(withdrawals_proxy, stranger):
    with reverts():
        stranger.transfer(withdrawals_proxy, '0.1 ether', data='0xaabbccdd', gas_limit=9_000_000)


def test_initial_admin_is_dao_voting(withdrawals_proxy, dao_voting):
    assert withdrawals_proxy.proxy_getAdmin() == dao_voting
    assert not withdrawals_proxy.proxy_getIsOssified()


def test_non_admin_cannot_change_implementation(withdrawals_proxy, new_impl, deployer, stranger):
    with reverts('proxy: unauthorized'):
        withdrawals_proxy.proxy_upgradeTo(new_impl, b'', {'from': deployer})

    with reverts('proxy: unauthorized'):
        withdrawals_proxy.proxy_upgradeTo(new_impl, b'', {'from': stranger})


def test_non_admin_cannot_change_admin(withdrawals_proxy, new_impl, deployer, stranger):
    with reverts('proxy: unauthorized'):
        withdrawals_proxy.proxy_changeAdmin(stranger, {'from': deployer})

    with reverts('proxy: unauthorized'):
        withdrawals_proxy.proxy_changeAdmin(deployer, {'from': stranger})


def test_voting_can_change_implementation(
    withdrawals_proxy,
    new_impl,
    helpers,
    Test__NewImplementation
):
    print(f'starting vote for withdrawals proxy upgrade...')

    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals_proxy.address,
        withdrawals_proxy.proxy_upgradeTo.encode_input(new_impl, b'')
    )
    tx = helpers.pass_and_exec_dao_vote(vote_id)

    assert withdrawals_proxy.implementation() == new_impl
    helpers.assert_single_event_named('Upgraded', tx, {'implementation': new_impl})

    withdrawals = Contract.from_abi(
        'Test__NewImplementation',
        withdrawals_proxy.address,
        Test__NewImplementation.abi
    )

    assert withdrawals.wasUpgraded()


def test_admin_can_call_implementation_methods(
    withdrawals_proxy,
    new_impl,
    helpers,
    Test__NewImplementation
):
    print(f'starting vote for withdrawals proxy upgrade...')

    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals_proxy.address,
        withdrawals_proxy.proxy_upgradeTo.encode_input(new_impl, b'')
    )
    helpers.pass_and_exec_dao_vote(vote_id)

    withdrawals = Contract.from_abi(
        'Test__NewImplementation',
        withdrawals_proxy.address,
        Test__NewImplementation.abi
    )

    print(f'starting vote for withdrawals method call...')

    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals.address,
        withdrawals.doSmth.encode_input()
    )
    tx = helpers.pass_and_exec_dao_vote(vote_id)

    helpers.assert_single_event_named('SmthHappened', tx)


def test_voting_can_change_admin(withdrawals_proxy, stranger, dao_voting, helpers):
    print(f'starting vote for withdrawals proxy admin change...')

    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals_proxy.address,
        withdrawals_proxy.proxy_changeAdmin.encode_input(stranger)
    )
    tx = helpers.pass_and_exec_dao_vote(vote_id)

    assert withdrawals_proxy.proxy_getAdmin() == stranger

    helpers.assert_single_event_named('AdminChanged', tx, {
        'previousAdmin': dao_voting,
        'newAdmin': stranger
    })


def test_voting_can_ossify_the_proxy(withdrawals_proxy, new_impl, helpers, dao_voting, deployer):
    print(f'starting vote for withdrawals proxy ossification...')
    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals_proxy.address,
        withdrawals_proxy.proxy_changeAdmin.encode_input(ZERO_ADDRESS)
    )
    tx = helpers.pass_and_exec_dao_vote(vote_id)

    assert withdrawals_proxy.proxy_getIsOssified()
    assert withdrawals_proxy.proxy_getAdmin() == ZERO_ADDRESS

    helpers.assert_single_event_named('AdminChanged', tx, {
        'previousAdmin': dao_voting,
        'newAdmin': ZERO_ADDRESS
    })

    with reverts('proxy: ossified'):
        withdrawals_proxy.proxy_upgradeTo(new_impl, b'', {'from': deployer})

    print(f'starting vote for withdrawals proxy upgrade...')
    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals_proxy.address,
        withdrawals_proxy.proxy_upgradeTo.encode_input(new_impl, b'')
    )

    with reverts('proxy: ossified'):
        helpers.pass_and_exec_dao_vote(vote_id)

    print(f'starting vote for withdrawals proxy admin change...')

    (vote_id, _) = helpers.start_vote_for_call(
        withdrawals_proxy.address,
        withdrawals_proxy.proxy_changeAdmin.encode_input(deployer)
    )

    with reverts('proxy: unauthorized'):
        helpers.pass_and_exec_dao_vote(vote_id)

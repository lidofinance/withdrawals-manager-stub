import pytest
from brownie import chain

from utils.evm_script import encode_call_script
from utils.voting import create_vote


@pytest.fixture(scope='function', autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture(scope='module')
def deployer(accounts):
    return accounts[0]


@pytest.fixture(scope='module')
def stranger(accounts):
    return accounts[9]


@pytest.fixture(scope='module')
def ldo_holder(accounts):
    return accounts.at('0xAD4f7415407B83a081A0Bee22D05A8FDC18B42da', force=True)


@pytest.fixture(scope='module')
def dao_voting(interface):
    return interface.Voting('0x2e59A20f205bB85a89C53f1936454680651E618e')


@pytest.fixture(scope='module')
def dao_token_manager(interface):
    return interface.TokenManager('0xf73a1260d222f447210581DDf212D915c09a3249')


class Helpers:
    accounts = None
    dao_voting = None
    dao_token_manager = None
    ldo_holder = None

    @staticmethod
    def filter_events_from(addr, events):
        return list(filter(lambda evt: evt.address == addr, events))

    @staticmethod
    def assert_single_event_named(evt_name, tx, evt_keys_dict = None, source = None):
        receiver_events = tx.events[evt_name]
        if source is not None:
            receiver_events = Helpers.filter_events_from(source, receiver_events)
        assert len(receiver_events) == 1
        if evt_keys_dict is not None:
            assert dict(receiver_events[0]) == evt_keys_dict
        return receiver_events[0]

    @staticmethod
    def assert_no_events_named(evt_name, tx):
        assert evt_name not in tx.events

    @staticmethod
    def start_vote_for_call(address, calldata):
        return create_vote(
            voting=Helpers.dao_voting,
            token_manager=Helpers.dao_token_manager,
            vote_desc=f'Test',
            evm_script=encode_call_script([(address, calldata)]),
            tx_params={'from': Helpers.ldo_holder}
        )

    @staticmethod
    def pass_and_exec_dao_vote(vote_id):
        print(f'executing vote {vote_id}')

        # together these accounts hold 15% of LDO total supply
        ldo_holders = [
            '0x3e40d73eb977dc6a537af587d48316fee66e9c8c',
            '0xb8d83908aab38a159f3da47a59d84db8e1838712',
            '0xa2dfc431297aee387c05beef507e5335e684fbcd'
        ]

        helper_acct = Helpers.accounts[0]

        for holder_addr in ldo_holders:
            print(f'voting from {holder_addr}')
            helper_acct.transfer(holder_addr, '0.1 ether')
            account = Helpers.accounts.at(holder_addr, force=True)
            Helpers.dao_voting.vote(vote_id, True, False, {'from': account})

        # wait for the vote to end
        chain.mine(timedelta=(3 * 60 * 60 * 24))

        assert Helpers.dao_voting.canExecute(vote_id)
        tx = Helpers.dao_voting.executeVote(vote_id, {'from': helper_acct})

        print(f'vote {vote_id} executed')
        return tx



@pytest.fixture(scope='module')
def helpers(accounts, dao_voting, dao_token_manager, ldo_holder):
    Helpers.accounts = accounts
    Helpers.dao_voting = dao_voting
    Helpers.dao_token_manager = dao_token_manager
    Helpers.ldo_holder = ldo_holder
    return Helpers

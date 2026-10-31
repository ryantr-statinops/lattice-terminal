import pytest
from pydantic import ValidationError
from kestrel_engine.broker import (
    BrokerAccount,
    BrokerAccountSnapshot,
    BrokerBalance,
    BrokerPosition,
    BrokerReadRequest,
    validate_broker_read_operation,
)


@pytest.mark.parametrize('operation', [
    'accounts.list', 'balance.read', 'positions.read', 'transactions.read', 'orders.read', 'fills.read',
])
def test_broker_read_allowlist_accepts_only_read_semantics(operation):
    request = BrokerReadRequest(
        provider_id='sample-broker',
        operation=operation,
        account_id=None if operation == 'accounts.list' else 'account-1',
    )
    assert validate_broker_read_operation(request.operation) == operation


@pytest.mark.parametrize('operation', ['orders.place', 'orders.cancel', 'orders.replace', 'transfer.create'])
def test_broker_read_allowlist_rejects_mutating_operations(operation):
    with pytest.raises(ValidationError):
        BrokerReadRequest(provider_id='sample-broker', operation=operation, account_id='account-1')
    with pytest.raises(ValueError, match='not allowlisted'):
        validate_broker_read_operation(operation)


def test_account_scoped_broker_read_requires_an_account_id():
    with pytest.raises(ValidationError, match='account_id is required'):
        BrokerReadRequest(provider_id='sample-broker', operation='positions.read')


def test_broker_account_identity_includes_provider_and_subaccount():
    first = BrokerAccount(
        provider_id='broker-a', account_id='12345', subaccount_id='cash',
        display_name='Cash book', account_type='cash', currency='VND',
    )
    second = first.model_copy(update={'subaccount_id': 'margin'})
    other_provider = first.model_copy(update={'provider_id': 'broker-b'})
    assert first.namespace_key == 'broker-a:12345:cash'
    assert len({first.namespace_key, second.namespace_key, other_provider.namespace_key}) == 3


def test_broker_account_rejects_invalid_currency_and_blank_identity():
    with pytest.raises(ValidationError, match='currency'):
        BrokerAccount(provider_id='broker-a', account_id='12345', display_name='Account', currency='vnd')
    with pytest.raises(ValidationError, match='must not be blank'):
        BrokerAccount(provider_id='broker-a', account_id=' ', display_name='Account')


def test_broker_account_snapshot_preserves_source_currency_and_asset_class():
    account = BrokerAccount(provider_id='broker-a', account_id='12345', display_name='Main')
    snapshot = BrokerAccountSnapshot(
        snapshot_id='snapshot-1', account=account,
        captured_at='2026-10-26T02:00:00Z', synced_at='2026-10-26T02:00:05Z',
        state='complete',
        balances=[BrokerBalance(currency='USD', cash_balance='12.50', available_cash='10.00')],
        positions=[BrokerPosition(
            provider_instrument_id='VN30F1M', asset_class='derivative', quantity='2',
            available_quantity='1', average_cost='1200.25', currency='VND',
        )],
    )
    assert snapshot.balances[0].currency == 'USD'
    assert snapshot.positions[0].asset_class == 'derivative'
    assert snapshot.positions[0].instrument_id is None


def test_partial_broker_snapshot_requires_missing_sections():
    account = BrokerAccount(provider_id='broker-a', account_id='12345', display_name='Main')
    fields = {
        'snapshot_id': 'snapshot-2', 'account': account,
        'captured_at': '2026-10-26T02:00:00Z', 'synced_at': '2026-10-26T02:00:05Z',
    }
    with pytest.raises(ValidationError, match='must list missing sections'):
        BrokerAccountSnapshot(**fields, state='partial')
    partial = BrokerAccountSnapshot(**fields, state='partial', missing_sections=['positions'])
    assert partial.state == 'partial'


def test_account_snapshot_rejects_float_money_and_complete_with_missing_data():
    account = BrokerAccount(provider_id='broker-a', account_id='12345', display_name='Main')
    with pytest.raises(ValidationError, match='valid string'):
        BrokerBalance(currency='VND', cash_balance=100.0)
    with pytest.raises(ValidationError, match='cannot have missing sections'):
        BrokerAccountSnapshot(
            snapshot_id='snapshot-3', account=account,
            captured_at='2026-10-26T02:00:00Z', synced_at='2026-10-26T02:00:05Z',
            state='complete', missing_sections=['positions'],
        )

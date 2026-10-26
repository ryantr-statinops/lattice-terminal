import pytest
from pydantic import ValidationError
from kestrel_engine.broker import BrokerReadRequest, validate_broker_read_operation


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

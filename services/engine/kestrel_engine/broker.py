"""Read-only broker account operation contracts."""
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .models import Record

BrokerReadOperation = Literal[
    'accounts.list',
    'balance.read',
    'positions.read',
    'transactions.read',
    'orders.read',
    'fills.read',
]

BROKER_READ_OPERATIONS = frozenset({
    'accounts.list',
    'balance.read',
    'positions.read',
    'transactions.read',
    'orders.read',
    'fills.read',
})


class BrokerReadRequest(Record):
    provider_id: str
    operation: BrokerReadOperation
    account_id: str | None = None

    @field_validator('provider_id', 'account_id')
    @classmethod
    def non_blank_identifiers(cls, value):
        if value is not None and not value.strip():
            raise ValueError('broker provider and account identifiers must not be blank')
        return value

    @model_validator(mode='after')
    def account_required_for_scoped_reads(self):
        if self.operation != 'accounts.list' and self.account_id is None:
            raise ValueError('account_id is required for account-scoped broker reads')
        return self


def validate_broker_read_operation(value: str) -> BrokerReadOperation:
    if value not in BROKER_READ_OPERATIONS:
        raise ValueError('broker operation is not allowlisted for read-only access')
    return value  # type: ignore[return-value]

"""Read-only broker account operation contracts."""
from typing import Literal
import re
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


class BrokerAccount(Record):
    """Provider-scoped account identity; subaccounts remain distinct local records."""

    provider_id: str
    account_id: str
    subaccount_id: str | None = None
    display_name: str
    account_type: str = 'unknown'
    currency: str | None = None

    @field_validator('provider_id', 'account_id', 'subaccount_id', 'display_name', 'account_type')
    @classmethod
    def non_blank_account_fields(cls, value):
        if value is not None and not value.strip():
            raise ValueError('broker account fields must not be blank')
        return value

    @field_validator('currency')
    @classmethod
    def valid_currency_code(cls, value):
        if value is not None and not re.fullmatch(r'[A-Z]{3}', value):
            raise ValueError('currency must be a three-letter uppercase code')
        return value

    @property
    def namespace_key(self) -> str:
        subaccount = self.subaccount_id or ''
        return f'{self.provider_id}:{self.account_id}:{subaccount}'


def validate_broker_read_operation(value: str) -> BrokerReadOperation:
    if value not in BROKER_READ_OPERATIONS:
        raise ValueError('broker operation is not allowlisted for read-only access')
    return value  # type: ignore[return-value]

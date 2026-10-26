"""Read-only broker account operation contracts."""
from typing import Literal
import re
from pydantic import AwareDatetime, Field, field_validator, model_validator
from .models import Record, decimal_text

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


class BrokerBalance(Record):
    currency: str
    cash_balance: str | None = None
    available_cash: str | None = None
    buying_power: str | None = None

    @field_validator('currency')
    @classmethod
    def valid_currency(cls, value):
        if not re.fullmatch(r'[A-Z]{3}', value):
            raise ValueError('currency must be a three-letter uppercase code')
        return value

    @field_validator('cash_balance', 'available_cash', 'buying_power')
    @classmethod
    def decimal_values(cls, value):
        if value is not None:
            decimal_text(value)
        return value


class BrokerPosition(Record):
    provider_instrument_id: str
    instrument_id: str | None = None
    asset_class: str = 'unknown'
    quantity: str
    available_quantity: str | None = None
    average_cost: str | None = None
    market_value: str | None = None
    currency: str | None = None

    @field_validator('provider_instrument_id', 'instrument_id', 'asset_class')
    @classmethod
    def non_blank_position_identity(cls, value):
        if value is not None and not value.strip():
            raise ValueError('position identity fields must not be blank')
        return value

    @field_validator('quantity', 'available_quantity', 'average_cost', 'market_value')
    @classmethod
    def decimal_values(cls, value):
        if value is not None:
            decimal_text(value)
        return value

    @field_validator('currency')
    @classmethod
    def valid_currency(cls, value):
        if value is not None and not re.fullmatch(r'[A-Z]{3}', value):
            raise ValueError('currency must be a three-letter uppercase code')
        return value


class BrokerAccountSnapshot(Record):
    snapshot_id: str
    account: BrokerAccount
    captured_at: AwareDatetime
    synced_at: AwareDatetime
    state: Literal['complete', 'partial', 'stale']
    balances: list[BrokerBalance] = Field(default_factory=list)
    positions: list[BrokerPosition] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    source_revision: str | None = None

    @field_validator('snapshot_id')
    @classmethod
    def non_blank_snapshot_id(cls, value):
        if not value.strip():
            raise ValueError('snapshot_id must not be blank')
        return value

    @model_validator(mode='after')
    def state_matches_missing_sections(self):
        if self.state == 'complete' and self.missing_sections:
            raise ValueError('complete account snapshot cannot have missing sections')
        if self.state == 'partial' and not self.missing_sections:
            raise ValueError('partial account snapshot must list missing sections')
        if len(set(self.missing_sections)) != len(self.missing_sections):
            raise ValueError('missing account sections must be unique')
        return self


def validate_broker_read_operation(value: str) -> BrokerReadOperation:
    if value not in BROKER_READ_OPERATIONS:
        raise ValueError('broker operation is not allowlisted for read-only access')
    return value  # type: ignore[return-value]

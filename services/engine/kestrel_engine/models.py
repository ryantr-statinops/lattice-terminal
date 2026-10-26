"""Versioned domain records. Money never crosses a boundary as a float."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

def decimal_text(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError('decimal fields must be strings')
    if len(value)>80 or not re.fullmatch(r'-?\d+(?:\.\d+)?',value):
        raise ValueError('use a plain finite decimal string of at most 80 characters')
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('invalid decimal') from error
    if not number.is_finite():
        raise ValueError('decimal must be finite')
    return value

class Record(BaseModel):
    model_config = ConfigDict(extra='forbid')
    @field_validator('*',mode='after')
    @classmethod
    def utc_instants(cls,value):
        if isinstance(value,datetime):
            if value.tzinfo is None:raise ValueError('timezone required')
            return value.astimezone(timezone.utc)
        return value

class Instrument(Record):
    id: str
    venue: str | None = None
    board: str
    native_symbol: str
    instrument_class: Literal[
        'equity', 'index', 'covered_warrant', 'derivative', 'bond', 'fund', 'etf',
        'fx', 'crypto', 'commodity', 'macro_series', 'real_estate', 'unknown',
    ] = 'unknown'
    name: str
    currency: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_id: str = 'SYNTHETIC-FIXTURE'
    is_synthetic: bool = True

class ProviderInstrumentAlias(Record):
    """Maps one provider's native instrument identifier to a stable local ID."""
    stable_instrument_id: str
    provider_id: str
    provider_instrument_id: str
    native_symbol: str
    venue: str | None = None

    @field_validator('stable_instrument_id', 'provider_id', 'provider_instrument_id', 'native_symbol')
    @classmethod
    def required_identity(cls, value):
        if not value.strip():
            raise ValueError('instrument identity fields must not be blank')
        return value

class Candle(Record):
    instrument_id: str
    interval: Literal['1m','5m','15m','30m','1h','1d','1w','1mo']
    open_time: AwareDatetime
    close_time: AwareDatetime
    available_at: AwareDatetime
    open: str
    high: str
    low: str
    close: str
    volume: str | None
    currency: str = 'unknown'
    price_unit: str = 'unknown'
    volume_unit: str = 'unknown'
    is_closed: bool
    revision: str
    session: str
    source_id: str = 'SYNTHETIC-FIXTURE'
    @field_validator('open','high','low','close')
    @classmethod
    def prices(cls,value):
        decimal_text(value)
        if Decimal(value)<=0: raise ValueError('price must be positive')
        return value
    @field_validator('volume')
    @classmethod
    def volumes(cls,value):
        if value is not None:
            decimal_text(value)
            if Decimal(value)<0: raise ValueError('negative volume')
        return value
    @model_validator(mode='after')
    def ordered(self):
        if self.open_time>=self.close_time: raise ValueError('invalid bar range')
        if self.is_closed and self.available_at<self.close_time: raise ValueError('closed bar available before close')
        if Decimal(self.low)>min(Decimal(self.open),Decimal(self.close)) or Decimal(self.high)<max(Decimal(self.open),Decimal(self.close)) or Decimal(self.low)>Decimal(self.high): raise ValueError('invalid OHLC envelope')
        return self

class Trade(Record):
    instrument_id: str
    trade_id: str
    event_time: AwareDatetime
    available_at: AwareDatetime
    price: str
    quantity: str
    currency: str = 'unknown'
    price_unit: str = 'unknown'
    quantity_unit: str = 'unknown'
    side: Literal['buy','sell','unknown'] = 'unknown'
    source_id: str
    revision: str = '0'

    @field_validator('price')
    @classmethod
    def valid_price(cls, value):
        decimal_text(value)
        if Decimal(value) <= 0:
            raise ValueError('trade price must be positive')
        return value

    @field_validator('quantity')
    @classmethod
    def valid_quantity(cls, value):
        decimal_text(value)
        if Decimal(value) <= 0:
            raise ValueError('trade quantity must be positive')
        return value

class Quote(Record):
    instrument_id: str
    event_time: AwareDatetime
    available_at: AwareDatetime
    bid_price: str | None = None
    bid_size: str | None = None
    ask_price: str | None = None
    ask_size: str | None = None
    currency: str = 'unknown'
    price_unit: str = 'unknown'
    size_unit: str = 'unknown'
    source_id: str
    revision: str = '0'

    @field_validator('bid_price', 'ask_price')
    @classmethod
    def valid_quote_prices(cls, value):
        if value is not None:
            decimal_text(value)
            if Decimal(value) <= 0:
                raise ValueError('quote price must be positive')
        return value

    @field_validator('bid_size', 'ask_size')
    @classmethod
    def valid_quote_sizes(cls, value):
        if value is not None:
            decimal_text(value)
            if Decimal(value) < 0:
                raise ValueError('quote size must not be negative')
        return value

    @model_validator(mode='after')
    def ordered_market(self):
        if self.bid_price is not None and self.ask_price is not None and Decimal(self.bid_price) > Decimal(self.ask_price):
            raise ValueError('bid price cannot exceed ask price')
        return self

class DepthLevel(Record):
    price: str
    quantity: str
    currency: str = 'unknown'
    price_unit: str = 'unknown'
    quantity_unit: str = 'unknown'
    order_count: int | None = None

    @field_validator('price')
    @classmethod
    def valid_depth_price(cls, value):
        decimal_text(value)
        if Decimal(value) <= 0:
            raise ValueError('depth price must be positive')
        return value

    @field_validator('quantity')
    @classmethod
    def valid_depth_quantity(cls, value):
        decimal_text(value)
        if Decimal(value) < 0:
            raise ValueError('depth quantity must not be negative')
        return value

class OrderBookDepth(Record):
    instrument_id: str
    event_time: AwareDatetime
    available_at: AwareDatetime
    bids: list[DepthLevel] = Field(default_factory=list)
    asks: list[DepthLevel] = Field(default_factory=list)
    source_id: str
    revision: str = '0'

    @model_validator(mode='after')
    def sorted_sides(self):
        if any(Decimal(a.price) < Decimal(b.price) for a, b in zip(self.bids, self.bids[1:])):
            raise ValueError('bid depth must be sorted highest price first')
        if any(Decimal(a.price) > Decimal(b.price) for a, b in zip(self.asks, self.asks[1:])):
            raise ValueError('ask depth must be sorted lowest price first')
        return self

class DatasetEnvelope(Record):
    provider_id: str
    dataset: str
    source_id: str
    observed_at: AwareDatetime
    available_at: AwareDatetime
    published_at: AwareDatetime | None = None
    revision: str
    schema_version: str
    parser_version: str
    unit: str = 'unknown'
    currency: str | None = None
    source_timezone: str = 'unknown'
    temporal_semantics: Literal[
        'event_time','observation_time','period_end','not_time_series','unknown',
    ] = 'unknown'
    adjustment_state: Literal['raw','adjusted','not_applicable','unknown'] = 'unknown'
    quality: Literal['complete','partial','stale','quarantined','unknown'] = 'unknown'
    payload: Any

class CorporateAction(Record):
    instrument_id: str
    action_id: str
    action_type: str
    announced_at: AwareDatetime
    ex_date: date | None = None
    record_date: date | None = None
    payment_date: date | None = None
    ratio: str | None = None
    cash_amount: str | None = None
    currency: str | None = None
    source_id: str
    revision: str = '0'

    @field_validator('ratio', 'cash_amount')
    @classmethod
    def valid_action_amounts(cls, value):
        if value is not None:
            decimal_text(value)
            if Decimal(value) < 0:
                raise ValueError('corporate action amounts must not be negative')
        return value

class FinancialStatement(Record):
    instrument_id: str
    statement_id: str
    statement_type: str
    period_start: date | None = None
    period_end: date
    published_at: AwareDatetime
    available_at: AwareDatetime
    currency: str
    unit: str
    values: dict[str, str]
    source_id: str
    revision: str = '0'

    @field_validator('values')
    @classmethod
    def finite_statement_values(cls, values):
        for value in values.values():
            decimal_text(value)
        return values

class ValueSeriesPoint(Record):
    series_id: str
    observation_time: AwareDatetime
    published_at: AwareDatetime | None = None
    available_at: AwareDatetime
    value: str
    unit: str
    currency: str | None = None
    geography: str | None = None
    source_id: str
    revision: str = '0'

    @field_validator('value')
    @classmethod
    def finite_series_value(cls, value):
        decimal_text(value)
        return value

class StrategySignal(Record):
    id: str
    run_id: str
    strategy_id: str
    instrument_id: str
    action: Literal['buy','sell','exit','reduce','custom']
    custom_action: str | None = None
    event_time: AwareDatetime
    price_context: dict[str, str] = Field(default_factory=dict)
    reason: str
    source: Literal['live','replay']
    logical_key: str
    correlation_id: str | None = None
    expires_at: AwareDatetime

    @field_validator('id','run_id','strategy_id','instrument_id','reason','logical_key','custom_action','correlation_id')
    @classmethod
    def non_blank_signal_fields(cls, value):
        if value is not None and not value.strip():
            raise ValueError('signal identity, reason, and logical key must not be blank')
        return value

    @field_validator('reason')
    @classmethod
    def bounded_reason(cls, value):
        if len(value) > 2000:
            raise ValueError('signal reason exceeds 2000 characters')
        return value

    @field_validator('logical_key')
    @classmethod
    def bounded_logical_key(cls, value):
        if len(value) > 200:
            raise ValueError('signal logical key exceeds 200 characters')
        return value

    @field_validator('price_context')
    @classmethod
    def decimal_price_context(cls, value):
        for item in value.values():
            decimal_text(item)
        return value

    @model_validator(mode='after')
    def valid_action_and_expiry(self):
        if self.action == 'custom' and self.custom_action is None:
            raise ValueError('custom signal requires custom_action')
        lifetime = self.expires_at - self.event_time
        if lifetime <= timedelta(0) or lifetime > timedelta(minutes=5):
            raise ValueError('signal expiry must be after event time and at most five minutes later')
        return self

class DataQuality(Record):
    state: Literal['fixture','complete','partial','stale','unavailable']
    gaps: list[str] = []
    adjustment: Literal['synthetic-unadjusted','unknown'] = 'synthetic-unadjusted'
    calendar: str = 'synthetic-weekdays-not-exchange-calendar'
    provisional_count: int = 0

class SourceCapability(Record):
    id: str
    documented: bool
    access_tested: bool
    rights_confirmed: bool
    approved: bool
    operating_state: Literal['fixture-only','scoped-probe','approved']
    reason: str

class MarketSnapshot(Record):
    schema_version: Literal['1','2'] = '2'
    snapshot_id: str
    instrument: Instrument
    quality: DataQuality
    candles: list[Candle]

def utc(value: datetime) -> str:
    if value.tzinfo is None: raise ValueError('timezone required')
    return value.astimezone(timezone.utc).isoformat()

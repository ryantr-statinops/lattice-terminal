"""Versioned domain records. Money never crosses a boundary as a float."""
from datetime import datetime, timezone
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
    venue: Literal['HOSE','HNX','UPCOM']
    board: str
    native_symbol: str
    instrument_class: Literal[
        'equity', 'index', 'covered_warrant', 'derivative', 'bond', 'fund', 'etf',
        'fx', 'crypto', 'commodity', 'macro_series', 'real_estate', 'unknown',
    ] = 'equity'
    name: str
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
    interval: Literal['1d','1m']
    open_time: AwareDatetime
    close_time: AwareDatetime
    available_at: AwareDatetime
    open: str
    high: str
    low: str
    close: str
    volume: str | None
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
    schema_version: Literal['1'] = '1'
    snapshot_id: str
    instrument: Instrument
    quality: DataQuality
    candles: list[Candle]

def utc(value: datetime) -> str:
    if value.tzinfo is None: raise ValueError('timezone required')
    return value.astimezone(timezone.utc).isoformat()

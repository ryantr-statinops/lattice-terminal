"""Shared provider contracts, capability metadata, and request pacing."""
"""Multi-provider abstractions for market data feeds (VNDIRECT, TCBS, DNSE, SSI, Local, Fixture)."""
from abc import ABC, abstractmethod
from datetime import date, datetime, time as daytime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import threading
import time
from typing import Any, Callable, Literal
import urllib.error
from urllib.parse import urlencode
import urllib.request
from pydantic import BaseModel, Field

from zoneinfo import ZoneInfo
from ..models import Candle, DailyIndexObservation, IndexConstituentSet, Instrument, ProviderIndexConstituent, decimal_text

def _is_retryable_read_error(error: Exception) -> bool:
    if isinstance(error, urllib.error.HTTPError):
        return error.code in (408, 425, 429) or 500 <= error.code <= 599
    return isinstance(error, (urllib.error.URLError, TimeoutError, ConnectionError))


def retry_read(
    operation: Callable[[], Any],
    *,
    retries: int = 2,
    base_backoff_seconds: float = 0.25,
    before_attempt: Callable[[], None] | None = None,
) -> Any:
    """Retry transient failures from idempotent provider reads with exponential backoff."""
    if retries < 0 or base_backoff_seconds < 0:
        raise ValueError('retry count and backoff must be non-negative')
    for attempt in range(retries + 1):
        if before_attempt is not None:
            before_attempt()
        try:
            return operation()
        except Exception as error:
            if attempt >= retries or not _is_retryable_read_error(error):
                raise
            time.sleep(base_backoff_seconds * (2 ** attempt))


class ProviderRequestLimiter:
    """Serialize outbound operations and pace requests for one provider."""

    def __init__(self, minimum_interval_seconds: float):
        if minimum_interval_seconds < 0:
            raise ValueError('minimum request interval cannot be negative')
        self.minimum_interval_seconds = minimum_interval_seconds
        self._last_request_at: float | None = None
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            if self._last_request_at is not None:
                delay = self.minimum_interval_seconds - (now - self._last_request_at)
                if delay > 0:
                    time.sleep(delay)
                    now = time.monotonic()
            self._last_request_at = now


class ProviderProbe(BaseModel):
    transport: Literal['reachable', 'unreachable']
    data: Literal['available', 'no_data', 'invalid', 'not_checked']
    symbol: str
    resolution: str
    sample_count: int | None = None
    first_bar_at: str | None = None
    last_bar_at: str | None = None

class ProviderStatus(BaseModel):
    id: str
    name: str
    category: Literal['community', 'broker_api', 'local', 'synthetic']
    state: Literal['connected', 'offline', 'blocked', 'fixture', 'unknown']
    latency_ms: float | None = None
    capabilities: list[str] = Field(default_factory=list)
    description: str = ''
    error: str | None = None
    configured: bool = True
    probe: ProviderProbe | None = None

class ProviderCapability(BaseModel):
    capability_id: str
    provider_id: str
    service: str
    dataset: str
    asset_class: str
    venue: str = 'unknown'
    venues: list[str] = Field(default_factory=list)
    documented: bool = False
    implemented: bool = False
    access_state: Literal['unknown', 'configured', 'available', 'blocked'] = 'unknown'
    rights_state: Literal['unknown', 'unverified', 'approved', 'denied'] = 'unknown'
    health_state: Literal['unknown', 'connected', 'offline', 'blocked'] = 'unknown'
    evidence: str = ''

class ProviderCapabilityRegistry:
    """Dataset-level claims kept separate from transient provider health."""

    def __init__(self):
        self._items: list[ProviderCapability] = []

        def add(provider_id: str, service: str, dataset: str, asset_class: str, venue: str, *,
                documented: bool, implemented: bool, rights_state: str = 'unknown', evidence: str = ''):
            capability_id = ':'.join((provider_id, service, dataset, asset_class, venue))
            self._items.append(ProviderCapability(
                capability_id=capability_id, provider_id=provider_id, service=service,
                dataset=dataset, asset_class=asset_class, venue=venue,
                venues=[] if venue == 'unknown' else [venue], documented=documented,
                implemented=implemented, access_state='unknown', rights_state=rights_state,
                health_state='unknown', evidence=evidence,
            ))

        for venue in ('HOSE', 'HNX', 'UPCOM'):
            for dataset in ('candles.1d', 'candles.1m'):
                add(
                    'vndirect', 'dchart-community', dataset, 'equity', venue,
                    documented=False, implemented=True, rights_state='unverified',
                    evidence='DChart UDF route is observed in the repository; official API and local-use rights are unverified.',
                )

        for venue in ('HOSE', 'HNX', 'UPCOM'):
            add(
                'tcbs', 'openapi', 'instruments.equity', 'equity', venue,
                documented=True, implemented=False, evidence='Official iFlash catalogue documents these equity venues; access and rights are unverified.',
            )
        for service, dataset, asset_class, evidence in (
            ('openapi', 'candles.intraday', 'equity', 'Official iFlash bars document minute/hour intervals; exact class coverage and rights are unverified.'),
            ('openapi', 'candles.long_term', 'equity', 'Official iFlash long-term bars document daily/weekly/monthly intervals; adjustments and rights are unverified.'),
            ('openapi', 'trades.history', 'equity', 'Official iFlash price-history endpoint documents paginated trade-like records; retention and semantics are unverified.'),
            ('community', 'candles', 'equity', 'Legacy TCBS community source is separate; current adapter refuses silent VNDIRECT substitution.'),
        ):
            add('tcbs', service, dataset, asset_class, 'unknown', documented=service == 'openapi', implemented=False, rights_state='unverified', evidence=evidence)

        for asset_class in ('equity', 'derivative', 'index'):
            add(
                'dnse', 'market-data', 'candles.ohlcv', asset_class, 'unknown',
                documented=True, implemented=False,
                evidence='DNSE public market-data catalogue documents historical OHLC by market family; exact venue, schema and rights require confirmation.',
            )
        for dataset, asset_class, venue, implemented, evidence in (
            ('instruments.details', 'equity', 'HOSE', True, 'SSI SecuritiesDetails documents stock security type and exchange fields; parser and local catalogue path implemented, access and rights remain unverified.'),
            ('instruments.details', 'equity', 'HNX', True, 'SSI SecuritiesDetails documents HNX stock security type and exchange fields; parser and local catalogue path implemented, access and rights remain unverified.'),
            ('instruments.details', 'equity', 'UPCOM', True, 'SSI SecuritiesDetails documents UPCOM stock security type and exchange fields; parser and local catalogue path implemented, access and rights remain unverified.'),
            ('instruments.details', 'covered_warrant', 'HOSE', True, 'SSI SecuritiesDetails documents CW and exchange fields; HOSE parser/path is offline-tested, but the class-venue mapping, access and rights still need entitled confirmation.'),
            ('instruments.details', 'derivative', 'DER', True, 'SSI SecuritiesDetails documents FU futures and DER exchange fields; DER parser/path is offline-tested, but the class-venue mapping, access and rights still need entitled confirmation.'),
            ('instruments.details', 'etf', 'HOSE', True, 'SSI SecuritiesDetails documents EF exchange-traded funds and exchange fields; HOSE parser/path is offline-tested, but the class-venue mapping, access and rights still need entitled confirmation.'),
            ('instruments.details', 'bond', 'HNXBOND', True, 'SSI SecuritiesDetails documents BO bonds and exchange fields; HNXBOND parser/path is offline-tested, but the class-venue mapping, access and rights still need entitled confirmation.'),
            ('instruments.index', 'index', 'HOSE', True, 'SSI IndexList documents HOSE index codes and names; parser and local catalogue path implemented, access and rights remain unverified.'),
            ('instruments.index', 'index', 'HNX', True, 'SSI IndexList documents HNX index codes and names; parser and local catalogue path implemented, access and rights remain unverified.'),
            ('indices.constituents', 'index', 'HOSE', True, 'SSI IndexComponents documents provider-reported HOSE membership snapshots; source security identifiers and historical effective dates remain unverified.'),
            ('indices.daily', 'index', 'HOSE', True, 'SSI DailyIndex documents HOSE daily index values and market aggregates; units, provider publication time and local-use rights remain unverified.'),
            ('indices.daily', 'index', 'HNX', True, 'SSI DailyIndex documents HNX daily index values and market aggregates; units, provider publication time and local-use rights remain unverified.'),
            ('candles.1d', 'equity', 'HOSE', True, 'SSI DailyOhlc documents paginated daily OHLCV; price units, publication timing, adjustments, account access and local-use rights remain unverified.'),
            ('candles.1d', 'equity', 'HNX', True, 'SSI DailyOhlc documents paginated daily OHLCV; HNX units, publication timing, adjustments, account access and local-use rights remain unverified.'),
            ('instruments.details', 'covered_warrant', 'unknown', False, 'SSI SecuritiesDetails documents CW security type; exact venue mapping requires account inventory.'),
            ('instruments.details', 'derivative', 'unknown', False, 'SSI SecuritiesDetails documents FU security type; contract lifecycle mapping requires account inventory.'),
            ('instruments.details', 'etf', 'unknown', False, 'SSI SecuritiesDetails documents EF security type; exact venue coverage requires account inventory.'),
            ('instruments.details', 'bond', 'unknown', False, 'SSI SecuritiesDetails documents BO security type; board and rights require account inventory.'),
            ('instruments.details', 'fund', 'unknown', False, 'SSI SecuritiesDetails documents OF and MF security types; exact venue and rights require account inventory.'),
        ):
            add('ssi', 'market-data', dataset, asset_class, venue, documented=True, implemented=implemented, rights_state='unverified', evidence=evidence)

    def list(self) -> list[ProviderCapability]:
        return list(self._items)

    def get(self, capability_id: str) -> ProviderCapability | None:
        return next((item for item in self._items if item.capability_id == capability_id), None)

    def source_ids(self) -> list:
        exact = [item.capability_id for item in self._items]
        legacy = [f'{item.provider_id}:{item.dataset}' for item in self._items]
        return list(dict.fromkeys([*exact, *legacy]))

class BaseMarketProvider(ABC):
    id: str
    name: str
    category: Literal['community', 'broker_api', 'local', 'synthetic']
    capabilities: list[str]
    description: str = ''

    def set_request_limiter(self, limiter: ProviderRequestLimiter) -> None:
        self._request_limiter = limiter

    def _read(self, operation: Callable[[], Any]) -> Any:
        limiter = getattr(self, '_request_limiter', None)
        before_attempt = limiter.acquire if limiter is not None else None
        return retry_read(operation, before_attempt=before_attempt)

    @abstractmethod
    def ping(self) -> ProviderStatus:
        """Check reachability and measure roundtrip latency in ms."""
        ...

    @abstractmethod
    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        """Fetch historical candles normalized to Kestrel Candle schema."""
        ...

    @abstractmethod
    def fetch_instruments(self) -> list[Instrument]:
        """List instruments supported by this provider."""
        ...

"""Synthetic fixture provider implementation."""
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

from .base import BaseMarketProvider, ProviderStatus

class SyntheticFixtureProvider(BaseMarketProvider):
    """Offline deterministic fixture data provider."""
    id = 'fixture'
    name = 'Synthetic Fixture'
    category = 'synthetic'
    capabilities = ['historical_candles', 'offline_replay']
    description = 'Safe offline fixtures stored locally in data/fixtures/. Always available.'

    def ping(self) -> ProviderStatus:
        return ProviderStatus(
            id=self.id,
            name=self.name,
            category=self.category,
            state='fixture',
            latency_ms=0.5,
            capabilities=self.capabilities,
            description=self.description,
            configured=True,
        )

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        return []

    def fetch_instruments(self) -> list[Instrument]:
        return []

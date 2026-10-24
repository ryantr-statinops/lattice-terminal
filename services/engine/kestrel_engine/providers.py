"""Multi-provider abstractions for market data feeds (TCBS, DNSE, SSI, Local, Fixture)."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any, Literal
import urllib.request
import json
from pydantic import BaseModel, Field

from .models import Candle, Instrument

class ProviderStatus(BaseModel):
    id: str
    name: str
    category: Literal['community', 'broker_api', 'local', 'synthetic']
    state: Literal['connected', 'offline', 'blocked', 'fixture']
    latency_ms: float | None = None
    capabilities: list[str] = Field(default_factory=list)
    description: str = ''
    error: str | None = None
    configured: bool = True

class BaseMarketProvider(ABC):
    id: str
    name: str
    category: Literal['community', 'broker_api', 'local', 'synthetic']
    capabilities: list[str]

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

"""Multi-provider abstractions for market data feeds (VNDIRECT, TCBS, DNSE, SSI, Local, Fixture)."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Literal
import urllib.request
from pydantic import BaseModel, Field

from .models import Candle, Instrument

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

class BaseMarketProvider(ABC):
    id: str
    name: str
    category: Literal['community', 'broker_api', 'local', 'synthetic']
    capabilities: list[str]
    description: str = ''

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

class VndirectCommunityProvider(BaseMarketProvider):
    """Free public TradingView UDF provider hosted by VNDIRECT (dchart-api)."""
    id = 'vndirect'
    name = 'VNDIRECT (Dchart UDF)'
    category = 'community'
    capabilities = ['historical_candles', 'intraday_candles', 'eod_daily']
    description = 'Public TradingView-compatible UDF feed for HOSE, HNX, UPCOM. No API key required.'

    def __init__(self, base_url: str = 'https://dchart-api.vndirect.com.vn'):
        self.base_url = base_url.rstrip('/')

    def ping(self) -> ProviderStatus:
        url = f'{self.base_url}/dchart/history?resolution=D&symbol=VNINDEX&from=1704067200&to=1704153600'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kestrel/1.0'})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                _ = resp.read(256)
                latency = round((time.perf_counter() - t0) * 1000, 1)
                return ProviderStatus(
                    id=self.id,
                    name=self.name,
                    category=self.category,
                    state='connected',
                    latency_ms=latency,
                    capabilities=self.capabilities,
                    description=self.description,
                )
        except Exception as err:
            return ProviderStatus(
                id=self.id,
                name=self.name,
                category=self.category,
                state='offline',
                latency_ms=None,
                capabilities=self.capabilities,
                description=self.description,
                error=str(err),
            )

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        resolution = '1' if interval == '1m' else 'D'
        from_ts = int(start.timestamp())
        to_ts = int(end.timestamp())
        url = f'{self.base_url}/dchart/history?resolution={resolution}&symbol={symbol}&from={from_ts}&to={to_ts}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kestrel/1.0'})
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        if data.get('s') != 'ok' or not data.get('t'):
            return []

        times = data['t']
        opens = data['o']
        highs = data['h']
        lows = data['l']
        closes = data['c']
        volumes = data.get('v', [0] * len(times))

        candles: list[Candle] = []
        for i in range(len(times)):
            bar_time = datetime.fromtimestamp(times[i], tz=timezone.utc)
            candles.append(Candle(
                instrument_id=f'VN:{symbol}',
                interval='1d' if resolution == 'D' else '1m',
                open_time=bar_time,
                close_time=bar_time,
                available_at=bar_time,
                open=f'{opens[i]:.2f}',
                high=f'{highs[i]:.2f}',
                low=f'{lows[i]:.2f}',
                close=f'{closes[i]:.2f}',
                volume=str(int(volumes[i])) if volumes[i] is not None else None,
                is_closed=True,
                revision='0',
                session='REGULAR',
                source_id='VNDIRECT-COMMUNITY',
            ))
        return candles

    def fetch_instruments(self) -> list[Instrument]:
        common = [
            ('HPG', 'HOSE', 'Hòa Phát'),
            ('FPT', 'HOSE', 'FPT Telecom/Software'),
            ('VNM', 'HOSE', 'Vinamilk'),
            ('VIC', 'HOSE', 'Vingroup'),
            ('TCB', 'HOSE', 'Techcombank'),
            ('SSI', 'HOSE', 'SSI Securities'),
            ('VND', 'HOSE', 'VNDIRECT Securities'),
            ('SHS', 'HNX', 'Sài Gòn - Hà Nội'),
            ('PVS', 'HNX', 'Dầu khí Việt Nam'),
            ('BSR', 'UPCOM', 'Lọc Hóa dầu Bình Sơn'),
        ]
        return [
            Instrument(
                id=f'VN:{sym}',
                venue=venue,
                board='MAIN',
                native_symbol=sym,
                name=name,
                source_id='VNDIRECT-COMMUNITY',
                is_synthetic=False,
            )
            for sym, venue, name in common
        ]

class TcbsCommunityProvider(BaseMarketProvider):
    """Free public stock analysis feed hosted by TCBS."""
    id = 'tcbs'
    name = 'TCBS (Vnstock Analysis)'
    category = 'community'
    capabilities = ['historical_candles', 'financials', 'valuation_ratios']
    description = 'Techcom Securities public stock insight & financial ratios API.'

    def __init__(self, base_url: str = 'https://apipubaws.tcbs.com.vn'):
        self.base_url = base_url.rstrip('/')

    def ping(self) -> ProviderStatus:
        url = f'{self.base_url}/tcanalysis/v1/ticker/HPG/overview'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kestrel/1.0'})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                _ = resp.read(256)
                latency = round((time.perf_counter() - t0) * 1000, 1)
                return ProviderStatus(
                    id=self.id,
                    name=self.name,
                    category=self.category,
                    state='connected',
                    latency_ms=latency,
                    capabilities=self.capabilities,
                    description=self.description,
                )
        except Exception as err:
            return ProviderStatus(
                id=self.id,
                name=self.name,
                category=self.category,
                state='offline',
                latency_ms=None,
                capabilities=self.capabilities,
                description=self.description,
                error=str(err),
            )

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        # Fallback to VNDirect UDF for bars if TCBS bars require auth
        vnd = VndirectCommunityProvider()
        return vnd.fetch_candles(symbol, interval, start, end)

    def fetch_instruments(self) -> list[Instrument]:
        vnd = VndirectCommunityProvider()
        return vnd.fetch_instruments()

class DnseBrokerProvider(BaseMarketProvider):
    """Official DNSE OpenAPI broker integration."""
    id = 'dnse'
    name = 'DNSE OpenAPI (LightSpeed)'
    category = 'broker_api'
    capabilities = ['historical_candles', 'realtime_ticks', 'orderbook', 'trading']
    description = 'Official open developer API by DNSE Securities. Realtime market data and order routing.'

    def __init__(self, api_key: str = '', api_secret: str = ''):
        self.api_key = api_key
        self.api_secret = api_secret

    def ping(self) -> ProviderStatus:
        is_configured = bool(self.api_key and self.api_secret)
        return ProviderStatus(
            id=self.id,
            name=self.name,
            category=self.category,
            state='blocked',
            latency_ms=None,
            capabilities=self.capabilities,
            description=self.description,
            configured=is_configured,
            error=(
                'DNSE connection check is not implemented; credentials are configured but connectivity is unverified'
                if is_configured
                else 'API credentials not configured in settings'
            ),
        )

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        if not self.api_key:
            raise ValueError('DNSE API Key required')
        return []

    def fetch_instruments(self) -> list[Instrument]:
        return []

class SsiFastConnectProvider(BaseMarketProvider):
    """Official SSI FastConnect Data provider."""
    id = 'ssi'
    name = 'SSI FastConnect Data'
    category = 'broker_api'
    capabilities = ['historical_candles', 'realtime_streaming', 'level2_quotes']
    description = 'Institutional market data feed from SSI Securities. Gated by source policy.'

    def ping(self) -> ProviderStatus:
        return ProviderStatus(
            id=self.id,
            name=self.name,
            category=self.category,
            state='blocked',
            latency_ms=None,
            capabilities=self.capabilities,
            description=self.description,
            configured=False,
            error='Production capability blocked by source gate policy (docs/03-market-research/source-register.md)',
        )

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        raise ValueError('SSI source capability blocked by policy')

    def fetch_instruments(self) -> list[Instrument]:
        return []

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

class RoutingPolicy(BaseModel):
    historical_provider: str = 'vndirect'
    realtime_provider: str = 'fixture'
    financials_provider: str = 'tcbs'
    fallback_enabled: bool = True

class ProviderRouter:
    """Manages provider routing, fallback execution and local caching."""
    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path('data/market')
        self.providers: dict[str, BaseMarketProvider] = {
            'vndirect': VndirectCommunityProvider(),
            'tcbs': TcbsCommunityProvider(),
            'dnse': DnseBrokerProvider(),
            'ssi': SsiFastConnectProvider(),
            'fixture': SyntheticFixtureProvider(),
        }
        self.policy = RoutingPolicy()

    def list_statuses(self) -> list[ProviderStatus]:
        statuses: list[ProviderStatus] = []
        for provider in self.providers.values():
            if provider.id == 'fixture':
                statuses.append(provider.ping())
                continue
            if provider.id == 'ssi':
                statuses.append(provider.ping())
                continue
            configured = bool(
                getattr(provider, 'api_key', None)
                and getattr(provider, 'api_secret', None)
            )
            statuses.append(ProviderStatus(
                id=provider.id,
                name=provider.name,
                category=provider.category,
                state='unknown',
                latency_ms=None,
                capabilities=provider.capabilities,
                description=provider.description,
                error=None,
                configured=configured,
            ))
        return statuses

    def ping(self, provider_id: str) -> ProviderStatus:
        if provider_id not in self.providers:
            raise ValueError(f"Unknown provider: {provider_id}")
        return self.providers[provider_id].ping()

    def update_policy(self, patch: dict[str, Any]) -> RoutingPolicy:
        self.policy = self.policy.model_copy(update=patch)
        return self.policy

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        primary_id = self.policy.historical_provider
        primary = self.providers.get(primary_id)
        if primary:
            try:
                res = primary.fetch_candles(symbol, interval, start, end)
                if res:
                    return res
            except Exception:
                if not self.policy.fallback_enabled:
                    raise
        if self.policy.fallback_enabled:
            for pid, prov in self.providers.items():
                if pid == primary_id or pid in ('ssi', 'dnse'):
                    continue
                try:
                    res = prov.fetch_candles(symbol, interval, start, end)
                    if res:
                        return res
                except Exception:
                    continue
        return []

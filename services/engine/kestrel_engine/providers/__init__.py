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

from .ssi import (SsiFastConnectProvider, normalize_ssi_der_derivative_catalogue, normalize_ssi_equity_catalogue, normalize_ssi_equity_daily_rows, normalize_ssi_hnx_daily_index_rows, normalize_ssi_hnx_equity_catalogue, normalize_ssi_hnx_equity_daily_rows, normalize_ssi_hose_covered_warrant_catalogue, normalize_ssi_hose_daily_index_rows, normalize_ssi_hose_equity_catalogue, normalize_ssi_hose_equity_daily_rows, normalize_ssi_hose_etf_catalogue, normalize_ssi_hose_index_catalogue, normalize_ssi_hose_index_components, normalize_ssi_hnxbond_bond_catalogue, normalize_ssi_index_catalogue, normalize_ssi_upcom_equity_catalogue)
from .base import (BaseMarketProvider, ProviderCapability, ProviderCapabilityRegistry, ProviderProbe, ProviderRequestLimiter, ProviderStatus, retry_read)

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
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30)
        symbol = 'VN:VNINDEX'
        url = f'{self.base_url}/dchart/history?{urlencode({"resolution":"D","symbol":symbol,"from":int(start.timestamp()),"to":int(now.timestamp())})}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kestrel/1.0'})
        t0 = time.perf_counter()
        try:
            with self._read(lambda: urllib.request.urlopen(req, timeout=4.0)) as resp:
                payload = json.loads(resp.read(1024 * 1024 + 1).decode('utf-8'))
                latency = round((time.perf_counter() - t0) * 1000, 1)
                data, count, first, last = self._probe_payload(payload)
                return ProviderStatus(
                    id=self.id,
                    name=self.name,
                    category=self.category,
                    state='connected' if data == 'available' else 'unknown',
                    latency_ms=latency,
                    capabilities=self.capabilities,
                    description=self.description,
                    probe=ProviderProbe(
                        transport='reachable',data=data,symbol=symbol,resolution='D',
                        sample_count=count,first_bar_at=first,last_bar_at=last,
                    ),
                    error='VNDIRECT endpoint returned no bars in the probe window' if data == 'no_data' else ('VNDIRECT returned an invalid UDF payload' if data == 'invalid' else None),
                )
        except urllib.error.HTTPError as err:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            return ProviderStatus(
                id=self.id,name=self.name,category=self.category,state='unknown',latency_ms=latency,
                capabilities=self.capabilities,description=self.description,
                probe=ProviderProbe(transport='reachable',data='invalid',symbol=symbol,resolution='D'),
                error=f'VNDIRECT endpoint responded with HTTP {err.code}',
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            latency = round((time.perf_counter() - t0) * 1000, 1)
            return ProviderStatus(
                id=self.id,name=self.name,category=self.category,state='unknown',latency_ms=latency,
                capabilities=self.capabilities,description=self.description,
                probe=ProviderProbe(transport='reachable',data='invalid',symbol=symbol,resolution='D'),
                error='VNDIRECT endpoint returned an invalid UDF payload',
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
                probe=ProviderProbe(transport='unreachable',data='not_checked',symbol=symbol,resolution='D'),
            )

    @staticmethod
    def _probe_payload(payload: Any) -> tuple[str, int | None, str | None, str | None]:
        if not isinstance(payload, dict):
            return 'invalid', None, None, None
        status = payload.get('s')
        if status == 'no_data':
            return 'no_data', 0, None, None
        if status != 'ok':
            return 'invalid', None, None, None
        columns = [payload.get(name) for name in ('t', 'o', 'h', 'l', 'c', 'v')]
        if any(not isinstance(column, list) for column in columns):
            return 'invalid', None, None, None
        count = len(columns[0])
        if count == 0:
            return 'invalid', None, None, None
        if any(len(column) != count for column in columns):
            return 'invalid', None, None, None
        times = columns[0]
        if any(not isinstance(value, int) or isinstance(value, bool) for value in times):
            return 'invalid', None, None, None
        if times != sorted(set(times)):
            return 'invalid', None, None, None
        try:
            for column in columns[1:]:
                for value in column:
                    number = Decimal(str(value))
                    if not number.is_finite():
                        return 'invalid', None, None, None
        except Exception:
            return 'invalid', None, None, None
        first = datetime.fromtimestamp(times[0], timezone.utc).isoformat()
        last = datetime.fromtimestamp(times[-1], timezone.utc).isoformat()
        return 'available', count, first, last

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        resolutions = {'1m': '1', '1d': 'D'}
        resolution = resolutions.get(interval)
        if resolution is None:
            raise ValueError(f'VNDIRECT does not support candle interval: {interval}')
        from_ts = int(start.timestamp())
        to_ts = int(end.timestamp())
        url = f'{self.base_url}/dchart/history?resolution={resolution}&symbol={symbol}&from={from_ts}&to={to_ts}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kestrel/1.0'})
        with self._read(lambda: urllib.request.urlopen(req, timeout=10.0)) as resp:
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
                instrument_class='equity',
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
            with self._read(lambda: urllib.request.urlopen(req, timeout=4.0)) as resp:
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
        raise NotImplementedError(
            'TCBS candle ingestion is not implemented; refusing to return VNDIRECT data as TCBS'
        )

    def fetch_instruments(self) -> list[Instrument]:
        raise NotImplementedError(
            'TCBS instrument ingestion is not implemented; refusing to return VNDIRECT instruments as TCBS'
        )

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
    datasets: dict[str, str] = Field(default_factory=dict)


ROUTING_CAPABILITY_GROUPS = {
    'historical_provider': {'historical_candles', 'intraday_candles', 'eod_daily'},
    'realtime_provider': {
        'realtime_ticks', 'realtime_streaming', 'quotes', 'orderbook', 'offline_replay',
    },
    'financials_provider': {'financials', 'valuation_ratios'},
}


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
        self.capabilities = ProviderCapabilityRegistry()
        # Conservative local pacing, not a claim about upstream quota values.
        # Replace each value only when that provider's documented limits are verified.
        self.request_limiters = {
            provider_id: ProviderRequestLimiter(0 if provider_id == 'fixture' else 1.0)
            for provider_id in self.providers
        }
        for provider_id, provider in self.providers.items():
            provider.set_request_limiter(self.request_limiters[provider_id])

    def list_statuses(self) -> list[ProviderStatus]:
        statuses: list[ProviderStatus] = []
        for provider in self.providers.values():
            if provider.id == 'fixture':
                statuses.append(provider.ping())
                continue
            if provider.id == 'ssi':
                configured = provider.configured
                statuses.append(ProviderStatus(
                    id=provider.id, name=provider.name, category=provider.category,
                    state='unknown' if configured else 'blocked', latency_ms=None,
                    capabilities=provider.capabilities, description=provider.description,
                    configured=configured,
                    error=None if configured else 'API credentials not configured in settings',
                ))
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

    def ping(self, provider_id: str, service: str | None = None, credential: dict[str, str] | None = None) -> ProviderStatus:
        if provider_id not in self.providers:
            raise ValueError(f"Unknown provider: {provider_id}")
        if credential is not None:
            if provider_id != 'ssi' or service != 'market-data':
                raise ValueError('credential probe is not supported for this provider service')
            self.providers[provider_id].configure_credentials(credential)
        return self.providers[provider_id].ping()

    def update_policy(self, patch: dict[str, Any]) -> RoutingPolicy:
        candidate = RoutingPolicy.model_validate(self.policy.model_dump() | patch)
        for route_key, capability_id in candidate.datasets.items():
            parts = route_key.rsplit(':', 2)
            if len(parts) != 3 or any(not part.strip() for part in parts):
                raise ValueError('dataset route key must be dataset:asset_class:venue')
            dataset, asset_class, venue = parts
            capability = self.capabilities.get(capability_id)
            if capability is None:
                raise ValueError(f'unknown dataset capability: {capability_id}')
            if (capability.dataset, capability.asset_class, capability.venue) != (dataset, asset_class, venue):
                raise ValueError('dataset route key does not match its selected capability')
            if not capability.implemented:
                raise ValueError(f'dataset capability has no implemented adapter: {capability_id}')
        for field, required_capabilities in ROUTING_CAPABILITY_GROUPS.items():
            provider_id = getattr(candidate, field)
            provider = self.providers.get(provider_id)
            if provider is None:
                raise ValueError(f'unknown provider for {field}: {provider_id}')
            if not required_capabilities.intersection(provider.capabilities):
                raise ValueError(f'{provider_id} does not declare {field} coverage')
        self.policy = candidate
        return candidate

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

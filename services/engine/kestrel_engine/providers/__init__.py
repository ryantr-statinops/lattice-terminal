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

from .community import DnseBrokerProvider, TcbsCommunityProvider, VndirectCommunityProvider
from .fixture import SyntheticFixtureProvider
from .ssi import (SsiFastConnectProvider, normalize_ssi_der_derivative_catalogue, normalize_ssi_equity_catalogue, normalize_ssi_equity_daily_rows, normalize_ssi_hnx_daily_index_rows, normalize_ssi_hnx_equity_catalogue, normalize_ssi_hnx_equity_daily_rows, normalize_ssi_hose_covered_warrant_catalogue, normalize_ssi_hose_daily_index_rows, normalize_ssi_hose_equity_catalogue, normalize_ssi_hose_equity_daily_rows, normalize_ssi_hose_etf_catalogue, normalize_ssi_hose_index_catalogue, normalize_ssi_hose_index_components, normalize_ssi_hnxbond_bond_catalogue, normalize_ssi_index_catalogue, normalize_ssi_upcom_equity_catalogue)
from .base import (BaseMarketProvider, ProviderCapability, ProviderCapabilityRegistry, ProviderProbe, ProviderRequestLimiter, ProviderStatus, retry_read)

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

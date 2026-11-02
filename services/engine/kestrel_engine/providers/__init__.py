"""Provider adapters and routing for normalized market data."""
import time
import urllib.error
import urllib.request

from .base import (BaseMarketProvider, ProviderCapability, ProviderCapabilityRegistry, ProviderProbe, ProviderRequestLimiter, ProviderStatus, retry_read)
from .community import DnseBrokerProvider, TcbsCommunityProvider, VndirectCommunityProvider
from .fixture import SyntheticFixtureProvider
from .registry import ROUTING_CAPABILITY_GROUPS, ProviderRouter, RoutingPolicy
from .ssi import (
    SsiFastConnectProvider,
    normalize_ssi_der_derivative_catalogue,
    normalize_ssi_equity_catalogue,
    normalize_ssi_equity_daily_rows,
    normalize_ssi_hnx_daily_index_rows,
    normalize_ssi_hnx_equity_catalogue,
    normalize_ssi_hnx_equity_daily_rows,
    normalize_ssi_hose_covered_warrant_catalogue,
    normalize_ssi_hose_daily_index_rows,
    normalize_ssi_hose_equity_catalogue,
    normalize_ssi_hose_equity_daily_rows,
    normalize_ssi_hose_etf_catalogue,
    normalize_ssi_hose_index_catalogue,
    normalize_ssi_hose_index_components,
    normalize_ssi_hnxbond_bond_catalogue,
    normalize_ssi_index_catalogue,
    normalize_ssi_upcom_equity_catalogue,
)

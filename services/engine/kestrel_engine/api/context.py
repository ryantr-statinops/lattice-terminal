"""Dependencies shared by internal API route groups."""
from dataclasses import dataclass
from pathlib import Path
from ..market_data.datasets import AtomicDatasetPublisher
from ..market_data.repository import MarketRepository
from ..market_data.sources import SourceGate
from ..providers import ProviderRouter
from ..runner import RunManager

@dataclass(frozen=True)
class EngineServices:
    market: MarketRepository
    runs: RunManager
    provider_router: ProviderRouter
    gate: SourceGate
    dataset_publisher: AtomicDatasetPublisher
    fixture_root: Path

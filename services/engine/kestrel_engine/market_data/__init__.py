"""Market repositories, immutable datasets, and revision handling."""
from .datasets import AtomicDatasetPublisher
from .repository import MarketRepository
from .revisions import deduplicate_revisions
from .archive import RightsAwareRawArchive
from .quarantine import RecordQuarantine
from .sources import Evidence, Scope, SourceBlocked, SourceGate

__all__ = ["AtomicDatasetPublisher", "Evidence", "MarketRepository", "RecordQuarantine", "RightsAwareRawArchive", "Scope", "SourceBlocked", "SourceGate", "deduplicate_revisions"]

"""Atomic Parquet snapshots for rights-approved normalized provider datasets."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from threading import RLock

import pyarrow as pa
import pyarrow.parquet as pq

from .models import DatasetEnvelope
from .sources import SourceGate

STORAGE_SCHEMA_VERSION = '1'
DATASET_SCHEMA = pa.schema([
    ('provider_id', pa.string()),
    ('dataset', pa.string()),
    ('source_id', pa.string()),
    ('observed_at', pa.timestamp('us', tz='UTC')),
    ('available_at', pa.timestamp('us', tz='UTC')),
    ('published_at', pa.timestamp('us', tz='UTC')),
    ('revision', pa.string()),
    ('schema_version', pa.string()),
    ('parser_version', pa.string()),
    ('unit', pa.string()),
    ('currency', pa.string()),
    ('source_timezone', pa.string()),
    ('temporal_semantics', pa.string()),
    ('adjustment_state', pa.string()),
    ('quality', pa.string()),
    ('payload_json', pa.string()),
])


def _field_names(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_field_names(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(_field_names(child) for child in value)) if value else set()
    return set()


class AtomicDatasetPublisher:
    def __init__(self, root: Path, source_gate: SourceGate):
        self.root = Path(root)
        self.source_gate = source_gate
        self._lock = RLock()

    def publish(self, capability_id: str, endpoint: str, envelopes: list[DatasetEnvelope]) -> dict[str, str | int]:
        if not envelopes:
            raise ValueError('dataset snapshot must contain at least one record')
        scope = self.source_gate.authorize(capability_id, 'store', endpoint)
        provider_ids = {record.provider_id for record in envelopes}
        datasets = {record.dataset for record in envelopes}
        if len(provider_ids) != 1 or len(datasets) != 1:
            raise ValueError('one snapshot must contain one provider and one dataset')
        provider_id, dataset = next(iter(provider_ids)), next(iter(datasets))
        if not capability_id.startswith(provider_id + ':'):
            raise ValueError('dataset provider does not match its source capability')

        rows = []
        canonical_records = []
        permitted_fields = set(scope.fields)
        for envelope in envelopes:
            payload_json = json.dumps(envelope.payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
            payload_document = json.loads(payload_json)
            if not _field_names(payload_document).issubset(permitted_fields):
                raise ValueError('normalized dataset contains fields outside the approved retention scope')
            if envelope.quality == 'quarantined':
                raise ValueError('quarantined records cannot be published in a dataset snapshot')
            canonical_records.append(envelope.model_dump(mode='json'))
            rows.append({
                'provider_id': envelope.provider_id,
                'dataset': envelope.dataset,
                'source_id': envelope.source_id,
                'observed_at': envelope.observed_at,
                'available_at': envelope.available_at,
                'published_at': envelope.published_at,
                'revision': envelope.revision,
                'schema_version': envelope.schema_version,
                'parser_version': envelope.parser_version,
                'unit': envelope.unit,
                'currency': envelope.currency,
                'source_timezone': envelope.source_timezone,
                'temporal_semantics': envelope.temporal_semantics,
                'adjustment_state': envelope.adjustment_state,
                'quality': envelope.quality,
                'payload_json': payload_json,
            })

        canonical_records.sort(key=lambda item: (
            item['available_at'], item['revision'],
            json.dumps(item['payload'], sort_keys=True, separators=(',', ':'), ensure_ascii=False),
        ))
        scope_identity = {
            'capability_id': capability_id,
            'endpoint': endpoint,
            'terms_reference': scope.terms_reference,
            'entitlement_reference': scope.entitlement_reference,
            'expires_at': scope.expires_at.isoformat(),
        }
        snapshot_id = hashlib.sha256(json.dumps(
            {'scope': scope_identity, 'records': canonical_records},
            sort_keys=True, separators=(',', ':'), ensure_ascii=False,
        ).encode('utf-8')).hexdigest()
        rows.sort(key=lambda item: (item['available_at'], item['revision'], item['payload_json']))

        root = self.root / 'datasets'
        target = root / snapshot_id
        with self._lock:
            if target.exists():
                manifest = self._load_manifest(target, snapshot_id)
                return {'snapshot_id': snapshot_id, 'row_count': manifest['row_count'], 'parquet_sha256': manifest['parquet_sha256'], 'terms_reference': manifest['terms_reference']}
            root.mkdir(parents=True, exist_ok=True)
            temporary = Path(tempfile.mkdtemp(prefix='.pending-', dir=root))
            try:
                parquet_path = temporary / 'records.parquet'
                pq.write_table(pa.Table.from_pylist(rows, schema=DATASET_SCHEMA), parquet_path, compression='zstd')
                parquet_hash = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
                available = [row['available_at'] for row in rows]
                manifest = {
                    'storage_schema_version': STORAGE_SCHEMA_VERSION,
                    'snapshot_id': snapshot_id,
                    **scope_identity,
                    'provider_id': provider_id,
                    'dataset': dataset,
                    'source_id': envelopes[0].source_id if len({record.source_id for record in envelopes}) == 1 else 'multiple',
                    'row_count': len(rows),
                    'parquet_sha256': parquet_hash,
                    'parser_versions': sorted({record.parser_version for record in envelopes}),
                    'quality': sorted({record.quality for record in envelopes}),
                    'available_from': min(available).isoformat(),
                    'available_to': max(available).isoformat(),
                }
                manifest_path = temporary / 'manifest.json'
                with manifest_path.open('w', encoding='utf-8', newline='\n') as output:
                    json.dump(manifest, output, sort_keys=True, indent=2, ensure_ascii=False)
                    output.flush()
                    os.fsync(output.fileno())
                with parquet_path.open('r+b') as output:
                    os.fsync(output.fileno())
                temporary.rename(target)
            except Exception:
                shutil.rmtree(temporary, ignore_errors=True)
                raise
        return {'snapshot_id': snapshot_id, 'row_count': len(rows), 'parquet_sha256': parquet_hash, 'terms_reference': scope.terms_reference}

    def _load_manifest(self, target: Path, snapshot_id: str) -> dict:
        manifest = json.loads((target / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('snapshot_id') != snapshot_id or manifest.get('storage_schema_version') != STORAGE_SCHEMA_VERSION:
            raise ValueError('dataset snapshot identity or schema version mismatch')
        parquet_path = target / 'records.parquet'
        if hashlib.sha256(parquet_path.read_bytes()).hexdigest() != manifest.get('parquet_sha256'):
            raise ValueError('dataset snapshot checksum mismatch')
        table = pq.read_table(parquet_path)
        if table.num_rows != manifest.get('row_count'):
            raise ValueError('dataset snapshot row count mismatch')
        return manifest

    def load(self, snapshot_id: str) -> tuple[dict, list[DatasetEnvelope]]:
        if len(snapshot_id) != 64 or any(value not in '0123456789abcdef' for value in snapshot_id):
            raise ValueError('invalid dataset snapshot identity')
        target = self.root / 'datasets' / snapshot_id
        manifest = self._load_manifest(target, snapshot_id)
        table = pq.read_table(target / 'records.parquet')
        envelopes = []
        for row in table.to_pylist():
            envelopes.append(DatasetEnvelope(
                provider_id=row['provider_id'], dataset=row['dataset'], source_id=row['source_id'],
                observed_at=row['observed_at'], available_at=row['available_at'], published_at=row['published_at'],
                revision=row['revision'], schema_version=row['schema_version'], parser_version=row['parser_version'],
                unit=row['unit'], currency=row['currency'], source_timezone=row['source_timezone'],
                temporal_semantics=row['temporal_semantics'], adjustment_state=row['adjustment_state'], quality=row['quality'],
                payload=json.loads(row['payload_json']),
            ))
        return manifest, envelopes

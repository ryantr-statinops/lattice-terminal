import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from kestrel_engine.datasets import AtomicDatasetPublisher
from kestrel_engine.models import DatasetEnvelope
from kestrel_engine.sources import SourceBlocked, SourceGate

CAPABILITY = 'ssi:market-data:instruments.equity:HOSE'


def gate(root: Path, *, approved=True, fields=None, expires_at='2999-01-01T00:00:00Z'):
    root.mkdir(parents=True, exist_ok=True)
    source_gate = SourceGate(root, [CAPABILITY])
    scope = {
        'endpoints': ['Market/Securities'],
        'purposes': ['store'],
        'fields': fields or ['symbol', 'name'],
        'request_limit': 10,
        'timeout_seconds': 6,
        'retention_allowed': True,
        'export_allowed': False,
        'terms_reference': 'terms-ssi-market',
        'entitlement_reference': 'entitlement-ssi',
        'expires_at': expires_at,
    }
    source_gate.path.write_text(json.dumps([{
        'id': CAPABILITY,
        'documented': True,
        'access_tested': True,
        'rights_confirmed': True,
        'approved': approved,
        'access_reference': 'access-ssi',
        'rights_reference': 'rights-ssi',
        'approval_reference': 'approval-ssi',
        'scope': scope,
    }]), encoding='utf-8')
    return source_gate


def envelope(symbol, name, available_at=None):
    instant = available_at or datetime(2026, 10, 27, 1, 0, tzinfo=timezone.utc)
    return DatasetEnvelope(
        provider_id='ssi', dataset='instruments.equity', source_id='SSI-FC-DATA',
        observed_at=instant, available_at=instant, revision='1', schema_version='1',
        parser_version='ssi-instruments-1', unit='instrument', source_timezone='Asia/Ho_Chi_Minh',
        temporal_semantics='not_time_series', quality='complete', payload={'symbol': symbol, 'name': name},
    )


def test_dataset_publisher_atomically_publishes_and_verifies_parquet(tmp_path):
    publisher = AtomicDatasetPublisher(tmp_path / 'market', gate(tmp_path))
    records = [envelope('AAA', 'Alpha'), envelope('BBB', 'Beta')]

    first = publisher.publish(CAPABILITY, 'Market/Securities', records)
    second = publisher.publish(CAPABILITY, 'Market/Securities', list(reversed(records)))
    manifest, loaded = publisher.load(first['snapshot_id'])

    assert first == second
    assert first['row_count'] == manifest['row_count'] == 2
    assert manifest['terms_reference'] == 'terms-ssi-market'
    assert {record.payload['symbol'] for record in loaded} == {'AAA', 'BBB'}
    assert not any(path.name.startswith('.pending-') for path in (tmp_path / 'market' / 'datasets').iterdir())
    registry = publisher.manifests(provider_id='ssi', dataset='instruments.equity')
    assert len(registry) == 1 and registry[0]['snapshot_id'] == first['snapshot_id']
    assert publisher.manifests(provider_id='other') == []


def test_dataset_publisher_fails_closed_without_rights_or_for_unapproved_fields(tmp_path):
    blocked = AtomicDatasetPublisher(tmp_path / 'blocked', gate(tmp_path / 'blocked-policy', approved=False))
    with pytest.raises(SourceBlocked):
        blocked.publish(CAPABILITY, 'Market/Securities', [envelope('AAA', 'Alpha')])
    assert not (tmp_path / 'blocked' / 'datasets').exists()

    restricted = AtomicDatasetPublisher(tmp_path / 'restricted', gate(tmp_path / 'restricted-policy', fields=['symbol']))
    with pytest.raises(ValueError, match='outside the approved retention scope'):
        restricted.publish(CAPABILITY, 'Market/Securities', [envelope('AAA', 'Alpha')])
    assert not (tmp_path / 'restricted' / 'datasets').exists()


def test_expired_dataset_snapshots_are_removed_and_cannot_be_loaded(tmp_path):
    now = datetime.now(timezone.utc)
    expiration = now.replace(microsecond=0)
    publisher = AtomicDatasetPublisher(tmp_path / 'market', gate(
        tmp_path, expires_at=(expiration + timedelta(hours=1)).isoformat(),
    ))
    expired = publisher.publish(CAPABILITY, 'Market/Securities', [envelope('OLD', 'Expired')])
    future = expiration + timedelta(hours=3)
    gate(tmp_path, expires_at=future.isoformat())
    retained = publisher.publish(CAPABILITY, 'Market/Securities', [envelope('NEW', 'Retained')])
    expiry_check = expiration + timedelta(hours=2)

    with pytest.raises(ValueError, match='retention authorization expired'):
        publisher.load(expired['snapshot_id'], now=expiry_check)
    assert publisher.prune_expired(now=expiry_check) == [expired['snapshot_id']]
    assert not (tmp_path / 'market' / 'datasets' / expired['snapshot_id']).exists()
    assert publisher.load(retained['snapshot_id'], now=expiry_check)[0]['snapshot_id'] == retained['snapshot_id']


def test_snapshot_identity_protects_retention_metadata_from_edits(tmp_path):
    publisher = AtomicDatasetPublisher(tmp_path / 'market', gate(tmp_path))
    snapshot = publisher.publish(CAPABILITY, 'Market/Securities', [envelope('AAA', 'Alpha')])
    manifest_path = tmp_path / 'market' / 'datasets' / snapshot['snapshot_id'] / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['expires_at'] = '2998-01-01T00:00:00+00:00'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')

    with pytest.raises(ValueError, match='snapshot identity mismatch'):
        publisher.load(snapshot['snapshot_id'])


def test_dataset_publisher_requires_one_provider_and_dataset_and_rejects_quarantine(tmp_path):
    publisher = AtomicDatasetPublisher(tmp_path / 'market', gate(tmp_path))
    mixed_provider = envelope('AAA', 'Alpha').model_copy(update={'provider_id': 'other'})
    with pytest.raises(ValueError, match='one provider and one dataset'):
        publisher.publish(CAPABILITY, 'Market/Securities', [envelope('AAA', 'Alpha'), mixed_provider])
    quarantined = envelope('BAD', 'Bad').model_copy(update={'quality': 'quarantined'})
    with pytest.raises(ValueError, match='quarantined records'):
        publisher.publish(CAPABILITY, 'Market/Securities', [quarantined])

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from kestrel_engine.archive import RightsAwareRawArchive
from kestrel_engine.sources import SourceBlocked, SourceGate


def approved_gate(root: Path, *, retention=True, expires=None):
    gate = SourceGate(root, ['ssi:market-data:instruments.equity:HOSE'])
    expiry = expires or datetime.now(timezone.utc) + timedelta(hours=1)
    scope = {
        'endpoints': ['Market/Securities'],
        'purposes': ['store'],
        'fields': ['data', 'symbol', 'StockName'],
        'request_limit': 10,
        'timeout_seconds': 6,
        'retention_allowed': retention,
        'export_allowed': False,
        'terms_reference': 'local-terms-check-17',
        'entitlement_reference': 'account-entitlement-4',
        'expires_at': expiry.isoformat(),
    }
    gate.path.write_text(json.dumps([{
        'id': 'ssi:market-data:instruments.equity:HOSE',
        'documented': True,
        'access_tested': True,
        'rights_confirmed': True,
        'approved': True,
        'access_reference': 'access-check-1',
        'rights_reference': 'contract-review-3',
        'approval_reference': 'approval-5',
        'scope': scope,
    }]), encoding='utf-8')
    return gate


def test_raw_archive_writes_only_under_exact_approved_retention_scope(tmp_path):
    payload = b'{"data":[{"symbol":"ACME"}]}'
    archive = RightsAwareRawArchive(tmp_path / 'store', approved_gate(tmp_path))

    record = archive.store('ssi:market-data:instruments.equity:HOSE', 'Market/Securities', payload)

    assert record['sha256'] == hashlib.sha256(payload).hexdigest()
    assert record['size_bytes'] == len(payload)
    assert record['terms_reference'] == 'local-terms-check-17'
    assert Path(record['path']).read_bytes() == payload
    assert archive.store('ssi:market-data:instruments.equity:HOSE', 'Market/Securities', payload) == record


@pytest.mark.parametrize('gate,endpoint', [
    (lambda root: SourceGate(root, ['ssi:market-data:instruments.equity:HOSE']), 'Market/Securities'),
    (lambda root: approved_gate(root, retention=False), 'Market/Securities'),
    (lambda root: approved_gate(root, expires=datetime.now(timezone.utc) - timedelta(seconds=1)), 'Market/Securities'),
    (lambda root: approved_gate(root), 'Market/DailyOhlc'),
])
def test_raw_archive_fails_closed_without_matching_retention_approval(tmp_path, gate, endpoint):
    source_gate = gate(tmp_path)
    archive_root = tmp_path / 'store'
    archive = RightsAwareRawArchive(archive_root, source_gate)

    with pytest.raises(SourceBlocked):
        archive.store('ssi:market-data:instruments.equity:HOSE', endpoint, b'raw')

    assert not (archive_root / 'raw').exists()


def test_raw_archive_rejects_empty_or_oversized_payload(tmp_path):
    archive = RightsAwareRawArchive(tmp_path / 'store', approved_gate(tmp_path))
    with pytest.raises(ValueError, match='non-empty'):
        archive.store('ssi:market-data:instruments.equity:HOSE', 'Market/Securities', b'')
    with pytest.raises(ValueError, match='64 MiB'):
        archive.store('ssi:market-data:instruments.equity:HOSE', 'Market/Securities', b'x' * (64 * 1024 * 1024 + 1))


def test_raw_archive_checks_every_json_field_against_approved_scope(tmp_path):
    gate = approved_gate(tmp_path)
    records = json.loads(gate.path.read_text(encoding='utf-8'))
    records[0]['scope']['fields'] = ['data', 'symbol']
    gate.path.write_text(json.dumps(records), encoding='utf-8')
    archive_root = tmp_path / 'store'
    archive = RightsAwareRawArchive(archive_root, gate)

    with pytest.raises(ValueError, match='outside the approved retention scope'):
        archive.store('ssi:market-data:instruments.equity:HOSE', 'Market/Securities', b'{"data":[{"symbol":"ACME","StockName":"Example"}]}')

    assert not (archive_root / 'raw').exists()

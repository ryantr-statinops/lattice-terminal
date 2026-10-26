import json
from pathlib import Path

import pytest

from kestrel_engine.archive import RightsAwareRawArchive
from kestrel_engine.quarantine import RecordQuarantine
from kestrel_engine.sources import SourceGate

CAPABILITY = 'ssi:market-data:instruments.equity:HOSE'


def authorized_archive(root: Path):
    gate = SourceGate(root, [CAPABILITY])
    gate.path.write_text(json.dumps([{
        'id': CAPABILITY,
        'documented': True,
        'access_tested': True,
        'rights_confirmed': True,
        'approved': True,
        'access_reference': 'access-1',
        'rights_reference': 'rights-1',
        'approval_reference': 'approval-1',
        'scope': {
            'endpoints': ['Market/Securities'],
            'purposes': ['store'],
            'fields': ['data', 'symbol', 'StockName'],
            'request_limit': 10,
            'timeout_seconds': 6,
            'retention_allowed': True,
            'export_allowed': False,
            'terms_reference': 'terms-1',
            'entitlement_reference': 'entitlement-1',
            'expires_at': '2999-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    return RightsAwareRawArchive(root / 'market', gate)


def test_quarantine_preserves_invalid_record_and_reason_metadata_under_rights_gate(tmp_path):
    record = b'{"data":[{"symbol":"BAD","StockName":null}]}'
    quarantine = RecordQuarantine(tmp_path / 'market', authorized_archive(tmp_path))

    first = quarantine.store(CAPABILITY, 'Market/Securities', 'instruments.equity', 'invalid_name', record)
    second = quarantine.store(CAPABILITY, 'Market/Securities', 'instruments.equity', 'invalid_name', record)

    assert first == second
    assert first['record_sha256']
    assert Path(first['raw_archive_path']).read_bytes() == record
    manifests = list((tmp_path / 'market' / 'quarantine').rglob('*.json'))
    assert len(manifests) == 1
    assert json.loads(manifests[0].read_text(encoding='utf-8'))['reason_code'] == 'invalid_name'
    raw_files = list((tmp_path / 'market' / 'raw').rglob('*.raw'))
    assert len(raw_files) == 1 and raw_files[0].read_bytes() == record


def test_quarantine_rejects_free_text_reason_without_storing_record(tmp_path):
    quarantine = RecordQuarantine(tmp_path / 'market', authorized_archive(tmp_path))
    with pytest.raises(ValueError, match='reason code'):
        quarantine.store(CAPABILITY, 'Market/Securities', 'instruments.equity', 'invalid name: token=private', b'{"data":[]}')
    assert not (tmp_path / 'market' / 'raw').exists()


def test_quarantine_obeys_raw_archive_field_allowlist(tmp_path):
    quarantine = RecordQuarantine(tmp_path / 'market', authorized_archive(tmp_path))
    with pytest.raises(ValueError, match='outside the approved retention scope'):
        quarantine.store(CAPABILITY, 'Market/Securities', 'instruments.equity', 'unknown_field', b'{"data":[{"symbol":"BAD","Secret":"value"}]}')
    assert not (tmp_path / 'market' / 'quarantine').exists()

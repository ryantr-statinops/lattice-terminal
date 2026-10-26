import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from kestrel_engine.app import create_app
from kestrel_engine.datasets import AtomicDatasetPublisher
from kestrel_engine.models import DatasetEnvelope
from kestrel_engine.providers import ProviderCapabilityRegistry
from kestrel_engine.sources import SourceGate


def test_market_reads_provider_catalogue_without_falling_back_to_fixtures(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:equity:unknown'
    source_id = 'SSI-FC-DATA'
    scope = {
        'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store'],
        'fields': ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin'],
        'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
        'export_allowed': False, 'terms_reference': 'terms-test', 'entitlement_reference': 'entitlement-test',
        'expires_at': '2099-01-01T00:00:00Z',
    }
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': scope,
    }]), encoding='utf-8')

    now = datetime.now(timezone.utc)
    publisher = AtomicDatasetPublisher(tmp_path / 'market', SourceGate(tmp_path, ProviderCapabilityRegistry().source_ids()))
    publisher.publish(capability_id, 'Market/SecuritiesDetails', [DatasetEnvelope(
        provider_id='ssi', dataset='instruments.details', source_id=source_id,
        observed_at=now, available_at=now, revision='1', schema_version='1', parser_version='ssi-details-1',
        unit='instrument', source_timezone='Asia/Ho_Chi_Minh', temporal_semantics='not_time_series',
        quality='complete', payload={
            'id': 'SSI:VN000000AAA1', 'venue': 'HOSE', 'board': 'unknown',
            'native_symbol': 'AAA', 'instrument_class': 'equity', 'name': 'Example JSC',
            'currency': 'VND', 'metadata': {'isin': 'VN000000AAA1'},
        },
    )])

    with TestClient(create_app('test-token', str(tmp_path))) as client:
        headers = {'Authorization': 'Bearer test-token'}
        provider = client.get('/internal/v1/market/instruments?provider_id=ssi', headers=headers)
        missing = client.get('/internal/v1/market/instruments?provider_id=dnse', headers=headers)
        fixture = client.get('/internal/v1/market/instruments', headers=headers)

    assert provider.status_code == 200
    assert provider.json() == [{
        'id': 'SSI:VN000000AAA1', 'venue': 'HOSE', 'board': 'unknown',
        'native_symbol': 'AAA', 'instrument_class': 'equity', 'name': 'Example JSC',
        'currency': 'VND', 'metadata': {'isin': 'VN000000AAA1'}, 'source_id': source_id,
        'is_synthetic': False,
    }]
    assert missing.status_code == 200 and missing.json() == []
    assert fixture.status_code == 200 and all(item['is_synthetic'] for item in fixture.json())

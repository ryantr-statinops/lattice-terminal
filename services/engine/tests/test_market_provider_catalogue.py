import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from kestrel_engine.app import create_app
from kestrel_engine.datasets import AtomicDatasetPublisher
from kestrel_engine.models import DatasetEnvelope, Instrument
from kestrel_engine.providers import ProviderCapabilityRegistry
from kestrel_engine.sources import SourceBlocked, SourceGate


def test_market_reads_provider_catalogue_without_falling_back_to_fixtures(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:equity:HOSE'
    source_id = 'SSI-FC-DATA'
    scope = {
        'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'],
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


def test_market_provider_catalogue_requires_explicit_display_rights(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:equity:HOSE'
    scope = {
        'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store'],
        'fields': ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata'],
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
        provider_id='ssi', dataset='instruments.details', source_id='SSI-FC-DATA',
        observed_at=now, available_at=now, revision='1', schema_version='1', parser_version='ssi-details-1',
        unit='instrument', source_timezone='Asia/Ho_Chi_Minh', temporal_semantics='not_time_series',
        quality='complete', payload={
            'id': 'SSI:VN000000AAA1', 'venue': 'HOSE', 'board': 'unknown',
            'native_symbol': 'AAA', 'instrument_class': 'equity', 'name': 'Example JSC',
            'currency': 'VND', 'metadata': {},
        },
    )])

    with pytest.raises(SourceBlocked, match='purpose/endpoint outside approved scope'):
        publisher.instrument_catalogue('ssi')


def test_ssi_hose_catalogue_ingest_checks_store_rights_then_publishes_snapshot(tmp_path, monkeypatch):
    capability_id = 'ssi:market-data:instruments.details:equity:HOSE'
    scope = {
        'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'],
        'fields': ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin', 'source_id', 'is_synthetic'],
        'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
        'export_allowed': False, 'terms_reference': 'terms-test', 'entitlement_reference': 'entitlement-test',
        'expires_at': '2099-01-01T00:00:00Z',
    }
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': scope,
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_hose_equity_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000AAA1', venue='HOSE', board='unknown', native_symbol='AAA',
            instrument_class='equity', name='Example JSC', metadata={'isin': 'VN000000AAA1'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )

    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-equity', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200 and catalogue.json()[0]['native_symbol'] == 'AAA'


def test_ssi_hose_catalogue_ingest_checks_store_rights_before_provider_access(tmp_path, monkeypatch):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_equity_catalogue = lambda **_: called.append(True)

    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-equity', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})

    assert response.status_code == 400
    assert not called

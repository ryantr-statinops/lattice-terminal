import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from kestrel_engine.app import create_app
from kestrel_engine.datasets import AtomicDatasetPublisher
from kestrel_engine.models import Candle, DailyIndexObservation, DatasetEnvelope, IndexConstituentSet, Instrument, ProviderIndexConstituent
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


def test_ssi_hnx_equity_catalogue_ingest_publishes_only_under_hnx_capability(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:equity:HNX'
    fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin', 'source_id', 'is_synthetic']
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_hnx_equity_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000HNX1', venue='HNX', board='unknown', native_symbol='HNXA',
            instrument_class='equity', name='HNX Alpha', metadata={'isin': 'VN000000HNX1'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hnx-equity', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['venue'] == 'HNX'
    assert catalogue.json()[0]['native_symbol'] == 'HNXA'


def test_ssi_hnx_equity_catalogue_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hnx_equity_catalogue = lambda **_: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hnx-equity', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_upcom_equity_catalogue_ingest_publishes_only_under_upcom_capability(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:equity:UPCOM'
    fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin', 'source_id', 'is_synthetic']
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_upcom_equity_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000UPC1', venue='UPCOM', board='unknown', native_symbol='UPCA',
            instrument_class='equity', name='UPCOM Alpha', metadata={'isin': 'VN000000UPC1'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/upcom-equity', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['venue'] == 'UPCOM'
    assert catalogue.json()[0]['native_symbol'] == 'UPCA'


def test_ssi_upcom_equity_catalogue_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_upcom_equity_catalogue = lambda **_: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/upcom-equity', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_hose_covered_warrant_ingest_publishes_only_under_covered_warrant_capability(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:covered_warrant:HOSE'
    fields = [
        'id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin',
        'underlying', 'put_or_call', 'exercise_price', 'exercise_ratio', 'maturity_date', 'lot_size',
        'source_id', 'is_synthetic',
    ]
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_hose_covered_warrant_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000CW01', venue='HOSE', board='unknown', native_symbol='CWA1',
            instrument_class='covered_warrant', name='Covered Alpha',
            metadata={'isin': 'VN000000CW01', 'underlying': 'AAA'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-covered-warrants', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['instrument_class'] == 'covered_warrant'
    assert catalogue.json()[0]['venue'] == 'HOSE'


def test_ssi_hose_covered_warrant_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_covered_warrant_catalogue = lambda **_: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-covered-warrants', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_der_futures_ingest_publishes_only_under_derivative_capability(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:derivative:DER'
    fields = [
        'id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin',
        'underlying', 'contract_multiplier', 'settlement_method', 'last_trading_date', 'maturity_date',
        'lot_size', 'source_id', 'is_synthetic',
    ]
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_der_derivative_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000FU01', venue='DER', board='unknown', native_symbol='VN30F1M',
            instrument_class='derivative', name='VN30 Futures',
            metadata={'isin': 'VN000000FU01', 'underlying': 'VN30'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/der-futures', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['instrument_class'] == 'derivative'
    assert catalogue.json()[0]['venue'] == 'DER'


def test_ssi_der_futures_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_der_derivative_catalogue = lambda **_: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/der-futures', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_hose_etf_ingest_publishes_only_under_etf_capability(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:etf:HOSE'
    fields = [
        'id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin',
        'issuer', 'issue_date', 'listed_share', 'source_id', 'is_synthetic',
    ]
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_hose_etf_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000ETF1', venue='HOSE', board='unknown', native_symbol='ETF1',
            instrument_class='etf', name='Example ETF',
            metadata={'isin': 'VN000000ETF1', 'issuer': 'Example AM'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-etfs', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['instrument_class'] == 'etf'
    assert catalogue.json()[0]['venue'] == 'HOSE'


def test_ssi_hose_etf_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_etf_catalogue = lambda **_: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-etfs', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_hnxbond_bond_ingest_publishes_only_under_bond_capability(tmp_path):
    capability_id = 'ssi:market-data:instruments.details:bond:HNXBOND'
    fields = [
        'id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'isin',
        'issuer', 'issue_date', 'maturity_date', 'lot_size', 'settlement_method', 'source_id', 'is_synthetic',
    ]
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': ['Market/SecuritiesDetails'], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    credential_seen = {}
    app.state.provider_router.providers['ssi'].fetch_hnxbond_bond_catalogue = lambda *, credential: (
        credential_seen.update(credential) or [Instrument(
            id='SSI:ISIN:VN000000BOND1', venue='HNXBOND', board='unknown', native_symbol='BOND1',
            instrument_class='bond', name='Example Bond',
            metadata={'isin': 'VN000000BOND1', 'issuer': 'Example Issuer'},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )]
    )
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hnxbond-bonds', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers={'Authorization': 'Bearer test-token'})

    assert response.status_code == 200
    assert response.json()['row_count'] == 1
    assert credential_seen == {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['instrument_class'] == 'bond'
    assert catalogue.json()[0]['venue'] == 'HNXBOND'


def test_ssi_hnxbond_bond_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hnxbond_bond_catalogue = lambda **_: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hnxbond-bonds', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_hose_daily_ohlc_ingest_publishes_and_reads_market_snapshot(tmp_path):
    catalogue_capability = 'ssi:market-data:instruments.details:equity:HOSE'
    daily_capability = 'ssi:market-data:candles.1d:equity:HOSE'
    expires = '2099-01-01T00:00:00Z'
    def evidence(capability_id, endpoint, fields, purposes):
        return {
            'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
            'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
            'approval_reference': 'approval-test', 'scope': {
                'endpoints': [endpoint], 'purposes': purposes, 'fields': fields,
                'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
                'export_allowed': False, 'terms_reference': 'terms-test',
                'entitlement_reference': 'entitlement-test', 'expires_at': expires,
            },
        }
    catalogue_fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'source_id', 'is_synthetic']
    candle_fields = ['instrument_id', 'interval', 'open_time', 'close_time', 'available_at', 'open', 'high', 'low', 'close', 'volume', 'currency', 'price_unit', 'volume_unit', 'is_closed', 'revision', 'session', 'source_id']
    (tmp_path / 'source-policy.json').write_text(json.dumps([
        evidence(catalogue_capability, 'Market/SecuritiesDetails', catalogue_fields, ['store', 'display']),
        evidence(daily_capability, 'Market/DailyOhlc', candle_fields, ['store', 'display']),
    ]), encoding='utf-8')

    now = datetime.now(timezone.utc)
    publisher = AtomicDatasetPublisher(tmp_path / 'market', SourceGate(tmp_path, ProviderCapabilityRegistry().source_ids()))
    publisher.publish(catalogue_capability, 'Market/SecuritiesDetails', [DatasetEnvelope(
        provider_id='ssi', dataset='instruments.details', source_id='SSI-FC-DATA',
        observed_at=now, available_at=now, revision='1', schema_version='1', parser_version='ssi-details-1',
        unit='instrument', source_timezone='Asia/Ho_Chi_Minh', temporal_semantics='not_time_series',
        quality='complete', payload={
            'id': 'SSI:VN000000AAA1', 'venue': 'HOSE', 'board': 'unknown',
            'native_symbol': 'AAA', 'instrument_class': 'equity', 'name': 'Example JSC',
            'currency': 'unknown', 'metadata': {}, 'source_id': 'SSI-FC-DATA', 'is_synthetic': False,
        },
    )])
    app = create_app('test-token', str(tmp_path))
    app.state.provider_router.update_policy({'datasets': {'candles.1d:equity:HOSE': daily_capability}})
    app.state.provider_router.providers['ssi'].fetch_hose_equity_daily = lambda instrument, start, end, *, credential: [Candle(
        instrument_id=instrument.id, interval='1d', open_time='2025-01-02T00:00:00+07:00',
        close_time='2025-01-03T00:00:00+07:00', available_at=now, open='10', high='12', low='9',
        close='11', volume='100', currency='unknown', price_unit='unknown', volume_unit='unknown',
        is_closed=True, revision='0', session='daily', source_id='SSI-FC-DATA',
    )]

    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer test-token'}
        response = client.post('/internal/v1/market/candles/ssi/hose-equity/daily', headers=headers, json={
            'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'},
            'instrument_id': 'SSI:VN000000AAA1', 'from_date': '2025-01-02', 'to_date': '2025-01-02',
        })
        market = client.get('/internal/v1/market/provider-candles?provider_id=ssi&instrument_id=SSI%3AVN000000AAA1', headers=headers)

    assert response.status_code == 200 and response.json()['row_count'] == 1
    assert market.status_code == 200
    assert market.json()['instrument']['native_symbol'] == 'AAA'
    assert market.json()['quality']['adjustment'] == 'unknown'
    assert market.json()['candles'][0]['open'] == '10'


def test_ssi_hose_index_catalogue_ingest_publishes_visible_index_instrument(tmp_path):
    capability_id = 'ssi:market-data:instruments.index:index:HOSE'
    endpoint = 'Market/IndexList'
    fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'index_code', 'exchange', 'source_id', 'is_synthetic']
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': [endpoint], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    app.state.provider_router.providers['ssi'].fetch_hose_index_catalogue = lambda *, credential: [Instrument(
        id='SSI:INDEX:HOSE:VN30', venue='HOSE', board='unknown', native_symbol='VN30',
        instrument_class='index', name='VN30', metadata={'index_code': 'VN30', 'exchange': 'HOSE'},
        source_id='SSI-FC-DATA', is_synthetic=False,
    )]

    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer test-token'}
        response = client.post('/internal/v1/market/catalogues/ssi/hose-indices', headers=headers, json={
            'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'},
        })
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers=headers)

    assert response.status_code == 200 and response.json()['row_count'] == 1
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['id'] == 'SSI:INDEX:HOSE:VN30'
    assert catalogue.json()[0]['instrument_class'] == 'index'
    assert catalogue.json()[0]['venue'] == 'HOSE'


def test_ssi_hose_index_catalogue_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_index_catalogue = lambda **kwargs: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hose-indices', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'id', 'consumerSecret': 'secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_hnx_index_catalogue_ingest_publishes_visible_hnx_index(tmp_path):
    capability_id = 'ssi:market-data:instruments.index:index:HNX'
    endpoint = 'Market/IndexList'
    fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'index_code', 'exchange', 'source_id', 'is_synthetic']
    (tmp_path / 'source-policy.json').write_text(json.dumps([{
        'id': capability_id, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
        'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
        'approval_reference': 'approval-test', 'scope': {
            'endpoints': [endpoint], 'purposes': ['store', 'display'], 'fields': fields,
            'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
            'export_allowed': False, 'terms_reference': 'terms-test',
            'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
        },
    }]), encoding='utf-8')
    app = create_app('test-token', str(tmp_path))
    app.state.provider_router.providers['ssi'].fetch_hnx_index_catalogue = lambda *, credential: [Instrument(
        id='SSI:INDEX:HNX:HNX30', venue='HNX', board='unknown', native_symbol='HNX30',
        instrument_class='index', name='HNX 30', metadata={'index_code': 'HNX30', 'exchange': 'HNX'},
        source_id='SSI-FC-DATA', is_synthetic=False,
    )]

    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer test-token'}
        response = client.post('/internal/v1/market/catalogues/ssi/hnx-indices', headers=headers, json={
            'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'},
        })
        catalogue = client.get('/internal/v1/market/instruments?provider_id=ssi', headers=headers)

    assert response.status_code == 200 and response.json()['row_count'] == 1
    assert catalogue.status_code == 200
    assert catalogue.json()[0]['id'] == 'SSI:INDEX:HNX:HNX30'
    assert catalogue.json()[0]['instrument_class'] == 'index'
    assert catalogue.json()[0]['venue'] == 'HNX'


def test_ssi_hnx_index_catalogue_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hnx_index_catalogue = lambda **kwargs: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/catalogues/ssi/hnx-indices', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'id', 'consumerSecret': 'secret'}})
    assert response.status_code == 400
    assert not called


def test_ssi_hose_index_components_publish_snapshot_and_require_explicit_routing(tmp_path):
    catalogue_capability = 'ssi:market-data:instruments.index:index:HOSE'
    capability_id = 'ssi:market-data:indices.constituents:index:HOSE'
    component_endpoint = 'Market/IndexComponents'
    catalogue_fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'index_code', 'exchange', 'source_id', 'is_synthetic']
    component_fields = [
        'index_instrument_id', 'index_code', 'index_name', 'exchange', 'reported_total_symbol_count',
        'constituents', 'provider_security_id', 'native_symbol', 'source_id', 'observed_at',
    ]
    policy = []
    for capability, endpoint, fields in (
        (catalogue_capability, 'Market/IndexList', catalogue_fields),
        (capability_id, component_endpoint, component_fields),
    ):
        policy.append({
            'id': capability, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
            'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
            'approval_reference': 'approval-test', 'scope': {
                'endpoints': [endpoint], 'purposes': ['store', 'display'], 'fields': fields,
                'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
                'export_allowed': False, 'terms_reference': 'terms-test',
                'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
            },
        })
    (tmp_path / 'source-policy.json').write_text(json.dumps(policy), encoding='utf-8')
    now = datetime.now(timezone.utc)
    publisher = AtomicDatasetPublisher(tmp_path / 'market', SourceGate(tmp_path, ProviderCapabilityRegistry().source_ids()))
    publisher.publish(catalogue_capability, 'Market/IndexList', [DatasetEnvelope(
        provider_id='ssi', dataset='instruments.index', source_id='SSI-FC-DATA',
        observed_at=now, available_at=now, revision='unknown', schema_version='1', parser_version='ssi-index-list-hose-1',
        unit='instrument', source_timezone='Asia/Ho_Chi_Minh', temporal_semantics='not_time_series',
        adjustment_state='not_applicable', quality='unknown', payload={
            'id': 'SSI:INDEX:HOSE:VN30', 'venue': 'HOSE', 'board': 'unknown', 'native_symbol': 'VN30',
            'instrument_class': 'index', 'name': 'VN30', 'currency': None,
            'metadata': {'index_code': 'VN30', 'exchange': 'HOSE'}, 'source_id': 'SSI-FC-DATA', 'is_synthetic': False,
        },
    )])
    app = create_app('test-token', str(tmp_path))
    app.state.provider_router.update_policy({'datasets': {'indices.constituents:index:HOSE': capability_id}})
    app.state.provider_router.providers['ssi'].fetch_hose_index_components = lambda index, *, credential: IndexConstituentSet(
        index_instrument_id=index.id, index_code='VN30', index_name='VN30', exchange='HOSE',
        reported_total_symbol_count=1, constituents=[ProviderIndexConstituent(provider_security_id='ACB', native_symbol='ACB')],
        source_id='SSI-FC-DATA', observed_at=now,
    )

    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer test-token'}
        published = client.post('/internal/v1/market/index-components/ssi/hose', headers=headers, json={
            'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'},
            'index_instrument_id': 'SSI:INDEX:HOSE:VN30',
        })
        result = client.get(
            '/internal/v1/market/provider-index-constituents?provider_id=ssi&index_instrument_id=SSI%3AINDEX%3AHOSE%3AVN30',
            headers=headers,
        )
        app.state.provider_router.update_policy({'datasets': {}})
        unrouted = client.get(
            '/internal/v1/market/provider-index-constituents?provider_id=ssi&index_instrument_id=SSI%3AINDEX%3AHOSE%3AVN30',
            headers=headers,
        )

    assert published.status_code == 200 and published.json()['row_count'] == 1
    assert result.status_code == 200
    assert result.json()['index']['native_symbol'] == 'VN30'
    assert result.json()['constituents']['constituents'][0]['provider_security_id'] == 'ACB'
    nested_time = datetime.fromisoformat(result.json()['constituents']['observed_at'].replace('Z', '+00:00'))
    envelope_time = datetime.fromisoformat(result.json()['observed_at'].replace('Z', '+00:00'))
    assert nested_time == envelope_time
    assert unrouted.status_code == 400


def test_ssi_hose_index_components_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_index_components = lambda *args, **kwargs: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/index-components/ssi/hose', headers={
            'Authorization': 'Bearer test-token',
        }, json={'credential': {'consumerID': 'id', 'consumerSecret': 'secret'}, 'index_instrument_id': 'SSI:INDEX:HOSE:VN30'})
    assert response.status_code == 400
    assert not called


@pytest.mark.parametrize(('venue', 'index_code'), [('HOSE', 'VN30'), ('HNX', 'HNX30')])
def test_ssi_daily_index_publishes_and_reads_routed_observations(tmp_path, venue, index_code):
    catalogue_capability = f'ssi:market-data:instruments.index:index:{venue}'
    capability_id = f'ssi:market-data:indices.daily:index:{venue}'
    catalogue_fields = ['id', 'venue', 'board', 'native_symbol', 'instrument_class', 'name', 'currency', 'metadata', 'index_code', 'exchange', 'source_id', 'is_synthetic']
    daily_fields = [
        'index_instrument_id', 'index_code', 'exchange', 'trading_date', 'provider_time', 'index_value',
        'change', 'ratio_change', 'total_trade', 'total_match_volume', 'total_match_value', 'type_index',
        'index_name', 'advances', 'no_changes', 'declines', 'ceilings', 'floors', 'total_deal_volume',
        'total_deal_value', 'total_volume', 'total_value', 'trading_session', 'provider_market',
        'provider_exchange', 'field_units', 'source_id', 'revision',
    ]
    policy = []
    for capability, endpoint, fields in (
        (catalogue_capability, 'Market/IndexList', catalogue_fields),
        (capability_id, 'Market/DailyIndex', daily_fields),
    ):
        policy.append({
            'id': capability, 'documented': True, 'access_tested': True, 'rights_confirmed': True,
            'approved': True, 'access_reference': 'access-test', 'rights_reference': 'rights-test',
            'approval_reference': 'approval-test', 'scope': {
                'endpoints': [endpoint], 'purposes': ['store', 'display'], 'fields': fields,
                'request_limit': 10, 'timeout_seconds': 6, 'retention_allowed': True,
                'export_allowed': False, 'terms_reference': 'terms-test',
                'entitlement_reference': 'entitlement-test', 'expires_at': '2099-01-01T00:00:00Z',
            },
        })
    (tmp_path / 'source-policy.json').write_text(json.dumps(policy), encoding='utf-8')
    now = datetime.now(timezone.utc)
    publisher = AtomicDatasetPublisher(tmp_path / 'market', SourceGate(tmp_path, ProviderCapabilityRegistry().source_ids()))
    publisher.publish(catalogue_capability, 'Market/IndexList', [DatasetEnvelope(
        provider_id='ssi', dataset='instruments.index', source_id='SSI-FC-DATA',
        observed_at=now, available_at=now, revision='unknown', schema_version='1', parser_version='ssi-index-list-hose-1',
        unit='instrument', source_timezone='Asia/Ho_Chi_Minh', temporal_semantics='not_time_series',
        adjustment_state='not_applicable', quality='unknown', payload={
            'id': f'SSI:INDEX:{venue}:{index_code}', 'venue': venue, 'board': 'unknown', 'native_symbol': index_code,
            'instrument_class': 'index', 'name': index_code, 'currency': None,
            'metadata': {'index_code': index_code, 'exchange': venue}, 'source_id': 'SSI-FC-DATA', 'is_synthetic': False,
        },
    )])
    app = create_app('test-token', str(tmp_path))
    route_key = f'indices.daily:index:{venue}'
    app.state.provider_router.update_policy({'datasets': {route_key: capability_id}})
    setattr(app.state.provider_router.providers['ssi'], f'fetch_{venue.casefold()}_daily_index', lambda index, start, end, *, credential: [DailyIndexObservation(
        index_instrument_id=index.id, index_code=index.native_symbol, exchange=venue, trading_date='2025-01-02',
        index_value='1320.50', change='-1.25', ratio_change='-0.09', total_trade='123',
        field_units={
            'index_value': 'provider_native_index_value_scale',
            'change': 'provider_native_index_change_scale',
            'ratio_change': 'provider_native_ratio_scale_unverified',
        }, source_id='SSI-FC-DATA',
    )])

    with TestClient(app) as client:
        headers = {'Authorization': 'Bearer test-token'}
        instrument_id = f'SSI:INDEX:{venue}:{index_code}'
        published = client.post(f'/internal/v1/market/index-series/ssi/{venue.casefold()}/daily', headers=headers, json={
            'credential': {'consumerID': 'local-id', 'consumerSecret': 'local-secret'},
            'index_instrument_id': instrument_id, 'from_date': '2025-01-02', 'to_date': '2025-01-02',
        })
        result = client.get(
            f'/internal/v1/market/provider-index-daily?provider_id=ssi&venue={venue}&index_instrument_id=SSI%3AINDEX%3A{venue}%3A{index_code}',
            headers=headers,
        )
        app.state.provider_router.update_policy({'datasets': {}})
        unrouted = client.get(
            f'/internal/v1/market/provider-index-daily?provider_id=ssi&venue={venue}&index_instrument_id=SSI%3AINDEX%3A{venue}%3A{index_code}',
            headers=headers,
        )

    assert published.status_code == 200, published.json()
    assert published.json()['row_count'] == 1
    assert result.status_code == 200
    assert result.json()['records'][0]['observation']['index_value'] == '1320.50'
    assert result.json()['records'][0]['observation']['exchange'] == venue
    assert result.json()['records'][0]['observation']['field_units']['index_value'] == 'provider_native_index_value_scale'
    assert unrouted.status_code == 400


def test_ssi_hose_daily_index_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_daily_index = lambda *args, **kwargs: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/index-series/ssi/hose/daily', headers={
            'Authorization': 'Bearer test-token',
        }, json={
            'credential': {'consumerID': 'id', 'consumerSecret': 'secret'},
            'index_instrument_id': 'SSI:INDEX:HOSE:VN30', 'from_date': '2025-01-02', 'to_date': '2025-01-02',
        })
    assert response.status_code == 400
    assert not called


def test_ssi_daily_ohlc_checks_store_rights_before_provider_access(tmp_path):
    app = create_app('test-token', str(tmp_path))
    called = []
    app.state.provider_router.providers['ssi'].fetch_hose_equity_daily = lambda *args, **kwargs: called.append(True)
    with TestClient(app) as client:
        response = client.post('/internal/v1/market/candles/ssi/hose-equity/daily', headers={
            'Authorization': 'Bearer test-token',
        }, json={
            'credential': {'consumerID': 'id', 'consumerSecret': 'secret'},
            'instrument_id': 'SSI:VN000000AAA1', 'from_date': '2025-01-02', 'to_date': '2025-01-02',
        })
    assert response.status_code == 400
    assert not called


def test_provider_daily_candle_read_requires_explicit_routing_policy(tmp_path):
    with TestClient(create_app('test-token', str(tmp_path))) as client:
        response = client.get(
            '/internal/v1/market/provider-candles?provider_id=ssi&instrument_id=SSI%3AVN000000AAA1',
            headers={'Authorization': 'Bearer test-token'},
        )
    assert response.status_code == 400
    assert response.json()['error'] == 'provider candle dataset is not selected in routing policy'

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from kestrel_engine.app import create_app
from kestrel_engine.datasets import AtomicDatasetPublisher
from kestrel_engine.models import Candle, DatasetEnvelope, Instrument
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

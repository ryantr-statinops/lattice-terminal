from fastapi.testclient import TestClient
from kestrel_engine.app import create_app
from kestrel_engine.providers import ProviderRouter, ProviderStatus

def test_health_is_offline_and_explicit():
    client = TestClient(create_app('test-token'))
    assert client.get('/internal/v1/health').status_code == 401
    response = client.get('/internal/v1/health', headers={'Authorization': 'Bearer test-token'})
    assert response.status_code == 200
    assert response.json()['mode'] == 'fixture-only'

def test_dataset_snapshot_registry_is_internal_and_empty_before_publish(tmp_path):
    with TestClient(create_app('test-token', str(tmp_path))) as client:
        assert client.get('/internal/v1/market/datasets').status_code == 401
        response = client.get('/internal/v1/market/datasets?provider_id=ssi',headers={'Authorization':'Bearer test-token'})
    assert response.status_code == 200
    assert response.json() == []

def test_ssi_provider_ping_receives_internal_credentials_without_echoing_them(monkeypatch):
    observed={}
    def ping(self,provider_id,service=None,credential=None):
        observed.update({'provider':provider_id,'service':service,'credential':credential})
        return ProviderStatus(id='ssi',name='SSI FastConnect Data',category='broker_api',state='connected',configured=True)
    monkeypatch.setattr(ProviderRouter,'ping',ping)
    with TestClient(create_app('test-token')) as client:
        response=client.post('/internal/v1/providers/ssi/ping',headers={'Authorization':'Bearer test-token'},json={
            'service':'market-data','credential':{'consumerID':'private-id','consumerSecret':'private-secret'},
        })
    assert response.status_code==200
    assert response.json()['state']=='connected'
    assert observed=={'provider':'ssi','service':'market-data','credential':{'consumerID':'private-id','consumerSecret':'private-secret'}}
    assert 'private-secret' not in response.text

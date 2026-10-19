from fastapi.testclient import TestClient
from kestrel_engine.app import create_app

def test_health_is_offline_and_explicit():
    client = TestClient(create_app('test-token'))
    assert client.get('/internal/v1/health').status_code == 401
    response = client.get('/internal/v1/health', headers={'Authorization': 'Bearer test-token'})
    assert response.status_code == 200
    assert response.json()['mode'] == 'fixture-only'

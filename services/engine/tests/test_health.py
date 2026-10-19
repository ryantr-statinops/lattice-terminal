from fastapi.testclient import TestClient
from kestrel_engine.app import create_app

def test_health_is_offline_and_explicit():
    response = TestClient(create_app()).get('/internal/v1/health')
    assert response.status_code == 200
    assert response.json()['mode'] == 'fixture-only'

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import FIXTURE_ROOT, create_app

@pytest.fixture
def client():
    return TestClient(create_app())

def test_health(client):
    assert client.get("/api/v1/health").json() == {"data": {"status": "ok", "service": "kestrel-terminal-api", "mode": "fixture"}, "meta": {"is_synthetic": True}}

def test_market_instruments(client):
    response = client.get("/api/v1/market/instruments")
    assert response.status_code == 200
    raw = json.loads((FIXTURE_ROOT / "market.json").read_text(encoding="utf-8"))
    assert response.json()["data"] == raw["instruments"]
    assert response.json()["meta"] == {"is_synthetic": True}

def test_market_candles(client):
    response = client.get("/api/v1/market/candles", params={"instrument_id": "binance:spot:BTCUSDT", "interval": "1h"})
    assert response.status_code == 200
    raw = json.loads((FIXTURE_ROOT / "market.json").read_text(encoding="utf-8"))
    expected = [c for c in raw["candles"] if c["instrument_id"] == "binance:spot:BTCUSDT" and c["interval"] == "1h"]
    assert response.json()["data"] == expected
    assert response.json()["meta"] == {"is_synthetic": True}

def test_market_candles_unknown_instrument(client):
    response = client.get("/api/v1/market/candles", params={"instrument_id": "nope", "interval": "1h"})
    assert response.status_code == 404

def test_news_articles(client):
    response = client.get("/api/v1/news/articles")
    assert response.status_code == 200
    raw = json.loads((FIXTURE_ROOT / "news.json").read_text(encoding="utf-8"))
    assert response.json()["data"] == raw["articles"]
    assert response.json()["meta"] == {"is_synthetic": True}

def test_news_articles_filter(client):
    response = client.get("/api/v1/news/articles", params={"instrument_id": "binance:spot:BTCUSDT"})
    assert response.status_code == 200
    raw = json.loads((FIXTURE_ROOT / "news.json").read_text(encoding="utf-8"))
    expected = [a for a in raw["articles"] if "binance:spot:BTCUSDT" in a["instrument_ids"]]
    assert response.json()["data"] == expected

def test_portfolio_holdings(client):
    response = client.get("/api/v1/portfolio/holdings")
    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"] == {"is_synthetic": True}

@pytest.mark.parametrize("content", [None, "{", '{"is_synthetic": false}', '{"is_synthetic": true}'])
def test_missing_or_invalid_fixture(tmp_path, content):
    if content is not None:
        (tmp_path / "news.json").write_text(content, encoding="utf-8")
    (tmp_path / "market.json").write_text(json.dumps(json.loads((FIXTURE_ROOT / "market.json").read_text())), encoding="utf-8")
    response = TestClient(create_app(tmp_path)).get("/api/v1/news/articles")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "fixture_unavailable"
    assert str(tmp_path) not in response.text

def test_non_synthetic_valid_shape_rejected(tmp_path):
    fixture = json.loads((FIXTURE_ROOT / "market.json").read_text(encoding="utf-8"))
    fixture["is_synthetic"] = False
    (tmp_path / "market.json").write_text(json.dumps(fixture), encoding="utf-8")
    (tmp_path / "news.json").write_text((FIXTURE_ROOT / "news.json").read_text(), encoding="utf-8")
    assert TestClient(create_app(tmp_path)).get("/api/v1/market/instruments").status_code == 503

def test_removed_routes(client):
    for path in ["/api/v1/admin/rooms", "/api/v1/auth/me", "/api/v1/rooms", "/api/v1/demo/news", "/api/v1/demo/market"]:
        response = client.get(path)
        assert response.status_code == 404
        assert "error" in response.json()

def test_read_only_and_no_cookie_cors(client):
    assert client.post("/api/v1/news/articles", json={}).status_code == 405
    response = client.get("/api/v1/news/articles", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in response.headers

def test_unexpected_failure_is_sanitized():
    app = create_app()
    @app.get("/failure")
    def failure():
        raise RuntimeError("private debugging details")
    response = TestClient(app, raise_server_exceptions=False).get("/failure")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private debugging details" not in response.text

import secrets
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .market import MarketRepository

def create_app(token: str | None = None, data_root: str | None = None) -> FastAPI:
    app = FastAPI(title="Kestrel Terminal internal engine", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.internal_token = token
    root = Path(data_root) if data_root else Path('.cache/engine-test-data')
    market = MarketRepository(root,Path(__file__).resolve().parents[3]/'data/fixtures')

    @app.middleware('http')
    async def internal_auth(request: Request, call_next):
        expected = app.state.internal_token
        actual = request.headers.get('authorization', '')
        if not expected or not secrets.compare_digest(actual, 'Bearer ' + expected):
            return JSONResponse({'error': 'unauthorized'}, status_code=401)
        return await call_next(request)

    @app.get("/internal/v1/health")
    def health():
        return {"service": "kestrel-engine", "status": "ok", "mode": "fixture-only"}

    @app.exception_handler(ValueError)
    async def invalid(request: Request,error: ValueError):
        return JSONResponse({'error':str(error)},status_code=400)

    @app.get('/internal/v1/market/instruments')
    def instruments(): return market.instruments()

    @app.get('/internal/v1/market/snapshots')
    def snapshots(): return market.manifests()

    @app.get('/internal/v1/market/candles')
    def candles(instrument_id:str): return market.latest_fixture(instrument_id)

    return app

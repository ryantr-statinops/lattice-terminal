"""Internal FastAPI application factory; route behavior lives in API groups."""
import secrets
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .market_data.repository import MarketRepository
from .market_data.datasets import AtomicDatasetPublisher
from .market_data.sources import SourceGate
from .providers import ProviderRouter
from .runner import RunManager
from .api.context import EngineServices
from .api.routes.analytics import build_analytics_router
from .api.routes.market_data import build_market_router
from .api.routes.paper import build_paper_router
from .api.routes.providers import build_provider_router
from .api.routes.runtime import build_runtime_router
from .api.routes.sources import build_sources_router

def create_app(token: str | None = None, data_root: str | None = None) -> FastAPI:
    app = FastAPI(title="Kestrel Terminal internal engine", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.internal_token = token
    root = Path(data_root) if data_root else Path('.cache/engine-test-data')
    fixture_root = Path(__file__).resolve().parents[3] / 'data/fixtures'
    market = MarketRepository(root, fixture_root)
    runs = RunManager(root)
    provider_router = ProviderRouter(root / 'market')
    gate = SourceGate(root, provider_router.capabilities.source_ids())
    dataset_publisher = AtomicDatasetPublisher(root / 'market', gate)
    dataset_publisher.prune_expired()
    app.state.dataset_publisher = dataset_publisher
    app.state.provider_router = provider_router
    services = EngineServices(market, runs, provider_router, gate, dataset_publisher, fixture_root)

    @app.on_event('shutdown')
    def stop_workers():
        runs.close()

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
    async def invalid(request: Request, error: ValueError):
        return JSONResponse({'error': str(error)}, status_code=400)

    for router in (
        build_provider_router(services),
        build_market_router(services),
        build_paper_router(services),
        build_sources_router(services),
        build_runtime_router(services),
        build_analytics_router(services),
    ):
        app.include_router(router)

    return app

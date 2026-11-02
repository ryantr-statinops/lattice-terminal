"""Source gate and live-feed status endpoints."""
from fastapi import APIRouter
from ..context import EngineServices

def build_sources_router(services: EngineServices) -> APIRouter:
    router = APIRouter()
    gate = services.gate
    @router.get('/internal/v1/sources')
    def sources(): return gate.status()

    @router.get('/internal/v1/market/live-status')
    def live_status():
        return {'state':'unavailable','reason':'SSI streaming and replay capability not approved; no live transport started','source_state':gate.status(),'reconciliation_required':True}

    return router

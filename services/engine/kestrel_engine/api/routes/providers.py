"""Provider status and routing endpoints."""
from typing import Any
from fastapi import APIRouter
from ..context import EngineServices
from ..schemas import ProviderPing
from ...providers import ProviderStatus

def build_provider_router(services: EngineServices) -> APIRouter:
    router = APIRouter()
    provider_router = services.provider_router
    @router.get("/internal/v1/providers")
    def list_providers():
        return provider_router.list_statuses()

    @router.get("/internal/v1/providers/capabilities")
    def list_provider_capabilities():
        return provider_router.capabilities.list()

    @router.post("/internal/v1/providers/{id}/ping",response_model=ProviderStatus)
    def ping_provider(id: str, value:ProviderPing|None=None):
        if value is None:return provider_router.ping(id)
        return provider_router.ping(id,value.service,value.credential)

    @router.get("/internal/v1/providers/routing")
    def get_routing():
        return provider_router.policy

    @router.put("/internal/v1/providers/routing")
    def update_routing(patch: dict[str, Any]):
        return provider_router.update_policy(patch)

    return router

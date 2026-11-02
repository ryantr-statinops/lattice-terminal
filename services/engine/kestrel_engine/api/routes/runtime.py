"""Program inspection and supervised runner endpoints."""
from fastapi import APIRouter
from ..context import EngineServices
from ..schemas import InspectRequest, RunRequest
from ...programs import inspect_source

def build_runtime_router(services: EngineServices) -> APIRouter:
    router = APIRouter()
    runs = services.runs
    @router.post('/internal/v1/programs/inspect')
    def inspect(value:InspectRequest):return inspect_source(value.source,value.kind,value.selected)

    @router.post('/internal/v1/runner/start',status_code=202)
    def start_run(value:RunRequest):runs.start(value.model_dump());return {'id':value.id}

    @router.get('/internal/v1/runner/{identity}/events')
    def run_events(identity:str,after:int=0):
        if after<0:raise ValueError('invalid cursor')
        return runs.events(identity,after)

    @router.post('/internal/v1/runner/{identity}/stop',status_code=202)
    def stop_run(identity:str):runs.cancel(identity);return {'status':'stop_requested'}

    return router

"""Market candle and quantitative analytics endpoints."""
from fastapi import APIRouter
from ..context import EngineServices
from ...analytics.quant import INDICATORS, calculate

def build_analytics_router(services: EngineServices) -> APIRouter:
    router = APIRouter()
    market = services.market
    @router.get('/internal/v1/market/candles')
    def candles(instrument_id:str): return market.latest_fixture(instrument_id)

    @router.get('/internal/v1/quant/indicators')
    def indicator_list(): return INDICATORS

    @router.get('/internal/v1/quant/calculate')
    def quant(instrument_id:str,indicator:str='sma',period:int=14,benchmark_id:str|None=None,annualization:int|None=None,snapshot_id:str|None=None):
        snapshot=market.load_for_instrument(snapshot_id,instrument_id) if snapshot_id else market.latest_fixture(instrument_id)
        benchmark=market.latest_fixture(benchmark_id).candles if benchmark_id else None
        if snapshot.quality.gaps: raise ValueError('resolve snapshot gaps before computing continuous indicators')
        return calculate(indicator,snapshot.candles,period,benchmark,annualization)|{'snapshot_id':snapshot.snapshot_id,'quality':snapshot.quality.model_dump()}

    return router

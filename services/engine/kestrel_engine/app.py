import secrets
from pathlib import Path
from datetime import date, datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .market import MarketRepository
from .datasets import AtomicDatasetPublisher
from .quant import INDICATORS,calculate
from .sources import SourceGate
from .providers import ProviderRouter
from .programs import inspect_source
from .runner import RunManager
from .models import DatasetEnvelope, Record
from .tapes import TapeRepository
from .execution import Order,validate_order,quote_fill
from decimal import Decimal
from typing import Any

class InspectRequest(Record):
    source:str
    kind:str
    selected:bool=False

class RunRequest(Record):
    id:str
    kind:str
    snapshot:str
    timeout_seconds:int=120

class PaperEvaluate(Record):
    snapshot:str
    after:int
    orders:list[dict[str,Any]]=[]

class PaperPrepare(Record):
    snapshot:str
    sequence:int
    id:str
    side:str
    limit_price:str
    quantity:str

class ProviderPing(Record):
    service:str='market-data'
    credential:dict[str,str]|None=None

class SsiCatalogueIngest(Record):
    credential:dict[str,str]

class SsiIndexCatalogueIngest(Record):
    credential:dict[str,str]

class SsiDailyOhlcIngest(Record):
    credential:dict[str,str]
    instrument_id:str
    from_date:date
    to_date:date

class SsiIndexComponentsIngest(Record):
    credential:dict[str,str]
    index_instrument_id:str

class SsiDailyIndexIngest(Record):
    credential:dict[str,str]
    index_instrument_id:str
    from_date:date
    to_date:date

def create_app(token: str | None = None, data_root: str | None = None) -> FastAPI:
    app = FastAPI(title="Kestrel Terminal internal engine", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.internal_token = token
    root = Path(data_root) if data_root else Path('.cache/engine-test-data')
    market = MarketRepository(root,Path(__file__).resolve().parents[3]/'data/fixtures')
    runs=RunManager(root)
    provider_router = ProviderRouter(root / 'market')
    gate=SourceGate(root,provider_router.capabilities.source_ids())
    dataset_publisher=AtomicDatasetPublisher(root/'market',gate)
    dataset_publisher.prune_expired()
    app.state.dataset_publisher=dataset_publisher
    app.state.provider_router=provider_router

    @app.on_event('shutdown')
    def stop_workers():runs.close()

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

    @app.get("/internal/v1/providers")
    def list_providers():
        return provider_router.list_statuses()

    @app.get("/internal/v1/providers/capabilities")
    def list_provider_capabilities():
        return provider_router.capabilities.list()

    @app.post("/internal/v1/providers/{id}/ping")
    def ping_provider(id: str, value:ProviderPing|None=None):
        if value is None:return provider_router.ping(id)
        return provider_router.ping(id,value.service,value.credential)

    @app.get("/internal/v1/providers/routing")
    def get_routing():
        return provider_router.policy

    @app.put("/internal/v1/providers/routing")
    def update_routing(patch: dict[str, Any]):
        return provider_router.update_policy(patch)

    @app.exception_handler(ValueError)
    async def invalid(request: Request,error: ValueError):
        return JSONResponse({'error':str(error)},status_code=400)

    @app.get('/internal/v1/market/instruments')
    def instruments(provider_id:str=''):
        if provider_id:
            return dataset_publisher.instrument_catalogue(provider_id)
        return market.instruments()

    @app.get('/internal/v1/market/snapshots')
    def snapshots(): return market.manifests()

    @app.get('/internal/v1/market/datasets')
    def dataset_snapshots(provider_id:str='',dataset:str=''):
        return dataset_publisher.manifests(provider_id,dataset)

    def _ingest_ssi_equity_catalogue(value:SsiCatalogueIngest,venue:str):
        capability_id=f'ssi:market-data:instruments.details:equity:{venue}'
        endpoint='Market/SecuritiesDetails'
        gate.authorize(capability_id,'store',endpoint)
        provider=provider_router.providers['ssi']
        fetch=getattr(provider,f'fetch_{venue.casefold()}_equity_catalogue')
        instruments=fetch(credential=value.credential)
        if not instruments:raise ValueError(f'SSI returned no {venue} equity instruments')
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.details',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='0',schema_version='1',
            parser_version=f'ssi-{venue.casefold()}-equity-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',quality='unknown',payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/catalogues/ssi/hose-equity')
    def ingest_ssi_hose_equity_catalogue(value:SsiCatalogueIngest):
        return _ingest_ssi_equity_catalogue(value,'HOSE')

    @app.post('/internal/v1/market/catalogues/ssi/hnx-equity')
    def ingest_ssi_hnx_equity_catalogue(value:SsiCatalogueIngest):
        return _ingest_ssi_equity_catalogue(value,'HNX')

    @app.post('/internal/v1/market/catalogues/ssi/upcom-equity')
    def ingest_ssi_upcom_equity_catalogue(value:SsiCatalogueIngest):
        return _ingest_ssi_equity_catalogue(value,'UPCOM')

    @app.post('/internal/v1/market/catalogues/ssi/hose-covered-warrants')
    def ingest_ssi_hose_covered_warrant_catalogue(value:SsiCatalogueIngest):
        capability_id='ssi:market-data:instruments.details:covered_warrant:HOSE'
        endpoint='Market/SecuritiesDetails'
        gate.authorize(capability_id,'store',endpoint)
        instruments=provider_router.providers['ssi'].fetch_hose_covered_warrant_catalogue(credential=value.credential)
        if not instruments:raise ValueError('SSI returned no HOSE covered warrants')
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.details',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='0',schema_version='1',
            parser_version='ssi-hose-covered-warrant-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',quality='unknown',payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/catalogues/ssi/der-futures')
    def ingest_ssi_der_derivative_catalogue(value:SsiCatalogueIngest):
        capability_id='ssi:market-data:instruments.details:derivative:DER'
        endpoint='Market/SecuritiesDetails'
        gate.authorize(capability_id,'store',endpoint)
        instruments=provider_router.providers['ssi'].fetch_der_derivative_catalogue(credential=value.credential)
        if not instruments:raise ValueError('SSI returned no DER futures')
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.details',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='0',schema_version='1',
            parser_version='ssi-der-derivative-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',quality='unknown',payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/catalogues/ssi/hose-etfs')
    def ingest_ssi_hose_etf_catalogue(value:SsiCatalogueIngest):
        capability_id='ssi:market-data:instruments.details:etf:HOSE'
        endpoint='Market/SecuritiesDetails'
        gate.authorize(capability_id,'store',endpoint)
        instruments=provider_router.providers['ssi'].fetch_hose_etf_catalogue(credential=value.credential)
        if not instruments:raise ValueError('SSI returned no HOSE ETFs')
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.details',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='0',schema_version='1',
            parser_version='ssi-hose-etf-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',quality='unknown',payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/catalogues/ssi/hnxbond-bonds')
    def ingest_ssi_hnxbond_bond_catalogue(value:SsiCatalogueIngest):
        capability_id='ssi:market-data:instruments.details:bond:HNXBOND'
        endpoint='Market/SecuritiesDetails'
        gate.authorize(capability_id,'store',endpoint)
        instruments=provider_router.providers['ssi'].fetch_hnxbond_bond_catalogue(credential=value.credential)
        if not instruments:raise ValueError('SSI returned no HNXBOND bonds')
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.details',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='0',schema_version='1',
            parser_version='ssi-hnxbond-bond-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',quality='unknown',payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/catalogues/ssi/hose-indices')
    def ingest_ssi_hose_index_catalogue(value:SsiIndexCatalogueIngest):
        capability_id='ssi:market-data:instruments.index:index:HOSE'
        endpoint='Market/IndexList'
        gate.authorize(capability_id,'store',endpoint)
        instruments=provider_router.providers['ssi'].fetch_hose_index_catalogue(credential=value.credential)
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.index',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='unknown',schema_version='1',
            parser_version='ssi-index-list-hose-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',adjustment_state='not_applicable',quality='unknown',
            payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/catalogues/ssi/hnx-indices')
    def ingest_ssi_hnx_index_catalogue(value:SsiIndexCatalogueIngest):
        capability_id='ssi:market-data:instruments.index:index:HNX'
        endpoint='Market/IndexList'
        gate.authorize(capability_id,'store',endpoint)
        instruments=provider_router.providers['ssi'].fetch_hnx_index_catalogue(credential=value.credential)
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='instruments.index',source_id=instrument.source_id,
            observed_at=observed_at,available_at=observed_at,revision='unknown',schema_version='1',
            parser_version='ssi-index-list-hnx-1',unit='instrument',source_timezone='Asia/Ho_Chi_Minh',
            temporal_semantics='not_time_series',adjustment_state='not_applicable',quality='unknown',
            payload=instrument.model_dump(mode='json'),
        ) for instrument in instruments]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/index-components/ssi/hose')
    def ingest_ssi_hose_index_components(value:SsiIndexComponentsIngest):
        capability_id='ssi:market-data:indices.constituents:index:HOSE'
        endpoint='Market/IndexComponents'
        gate.authorize(capability_id,'store',endpoint)
        index=next((item for item in dataset_publisher.instrument_catalogue(
            'ssi','ssi:market-data:instruments.index:index:HOSE',
        ) if item.id==value.index_instrument_id),None)
        if index is None or index.instrument_class!='index' or index.venue!='HOSE':
            raise ValueError('index is not present in the authorized SSI HOSE index catalogue')
        constituents=provider_router.providers['ssi'].fetch_hose_index_components(index,credential=value.credential)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='indices.constituents',source_id=constituents.source_id,
            observed_at=constituents.observed_at,available_at=constituents.observed_at,revision='unknown',
            schema_version='1',parser_version='ssi-index-components-hose-1',unit='constituents',
            source_timezone='Asia/Ho_Chi_Minh',temporal_semantics='observation_time',
            adjustment_state='not_applicable',quality='unknown',payload=constituents.model_dump(mode='json'),
        )]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    def _ingest_ssi_daily_index(value:SsiDailyIndexIngest,venue:str):
        capability_id=f'ssi:market-data:indices.daily:index:{venue}'
        endpoint='Market/DailyIndex'
        gate.authorize(capability_id,'store',endpoint)
        if value.from_date>value.to_date:raise ValueError('SSI DailyIndex date range is invalid')
        index=next((item for item in dataset_publisher.instrument_catalogue(
            'ssi',f'ssi:market-data:instruments.index:index:{venue}',
        ) if item.id==value.index_instrument_id),None)
        if index is None or index.instrument_class!='index' or index.venue!=venue:
            raise ValueError(f'index is not present in the authorized SSI {venue} index catalogue')
        fetch=getattr(provider_router.providers['ssi'],f'fetch_{venue.casefold()}_daily_index')
        observations=fetch(
            index,value.from_date,value.to_date,credential=value.credential,
        )
        if not observations:raise ValueError(f'SSI returned no {venue} daily index observations')
        observed_at=datetime.now(timezone.utc)
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='indices.daily',source_id=observation.source_id,
            observed_at=observed_at,available_at=observed_at,revision=observation.revision,
            schema_version='1',parser_version=f'ssi-daily-index-{venue.casefold()}-1',unit='field_specific',
            source_timezone='Asia/Ho_Chi_Minh',temporal_semantics='observation_time',
            adjustment_state='not_applicable',quality='unknown',payload=observation.model_dump(mode='json'),
        ) for observation in observations]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/index-series/ssi/hose/daily')
    def ingest_ssi_hose_daily_index(value:SsiDailyIndexIngest):
        return _ingest_ssi_daily_index(value,'HOSE')

    @app.post('/internal/v1/market/index-series/ssi/hnx/daily')
    def ingest_ssi_hnx_daily_index(value:SsiDailyIndexIngest):
        return _ingest_ssi_daily_index(value,'HNX')

    def _ingest_ssi_equity_daily(value:SsiDailyOhlcIngest,venue:str):
        capability_id=f'ssi:market-data:candles.1d:equity:{venue}'
        endpoint='Market/DailyOhlc'
        gate.authorize(capability_id,'store',endpoint)
        if value.from_date>value.to_date:raise ValueError('SSI DailyOhlc date range is invalid')
        instrument=next((item for item in dataset_publisher.instrument_catalogue('ssi') if item.id==value.instrument_id),None)
        if instrument is None:raise ValueError('instrument is not present in the authorized provider catalogue')
        provider=provider_router.providers['ssi']
        fetch=getattr(provider,f'fetch_{venue.casefold()}_equity_daily')
        candles=fetch(instrument,value.from_date,value.to_date,credential=value.credential)
        if not candles:raise ValueError(f'SSI returned no {venue} daily candles')
        envelopes=[DatasetEnvelope(
            provider_id='ssi',dataset='candles.1d',source_id=candle.source_id,
            observed_at=candle.available_at,available_at=candle.available_at,revision=candle.revision,
            schema_version='1',parser_version='ssi-daily-ohlc-1',unit='unknown',
            currency=None,source_timezone='Asia/Ho_Chi_Minh',temporal_semantics='period_end',
            adjustment_state='unknown',quality='unknown',payload=candle.model_dump(mode='json'),
        ) for candle in candles]
        return dataset_publisher.publish(capability_id,endpoint,envelopes)

    @app.post('/internal/v1/market/candles/ssi/hose-equity/daily')
    def ingest_ssi_hose_equity_daily(value:SsiDailyOhlcIngest):
        return _ingest_ssi_equity_daily(value,'HOSE')

    @app.post('/internal/v1/market/candles/ssi/hnx-equity/daily')
    def ingest_ssi_hnx_equity_daily(value:SsiDailyOhlcIngest):
        return _ingest_ssi_equity_daily(value,'HNX')

    @app.get('/internal/v1/market/provider-candles')
    def provider_candles(provider_id:str,instrument_id:str,venue:str):
        venue=venue.strip().upper()
        if venue not in {'HOSE','HNX'}:raise ValueError('provider daily candles support only HOSE and HNX venues')
        route_key=f'candles.1d:equity:{venue}'
        capability_id=f'{provider_id}:market-data:{route_key}'
        if provider_router.policy.datasets.get(route_key)!=capability_id:
            raise ValueError('provider candle dataset is not selected in routing policy')
        instrument=next((item for item in dataset_publisher.instrument_catalogue(provider_id) if item.id==instrument_id),None)
        if instrument is None or instrument.instrument_class!='equity' or instrument.venue!=venue:
            raise ValueError('instrument is not present in the selected provider candle venue catalogue')
        return dataset_publisher.candle_snapshot(provider_id,instrument_id)

    @app.get('/internal/v1/market/provider-index-constituents')
    def provider_index_constituents(provider_id:str,index_instrument_id:str):
        route_key='indices.constituents:index:HOSE'
        capability_id=f'{provider_id}:market-data:{route_key}'
        if provider_router.policy.datasets.get(route_key)!=capability_id:
            raise ValueError('provider index constituent dataset is not selected in routing policy')
        return dataset_publisher.index_constituent_snapshot(provider_id,index_instrument_id)

    @app.get('/internal/v1/market/provider-index-daily')
    def provider_index_daily(provider_id:str,index_instrument_id:str,venue:str):
        route_key=f'indices.daily:index:{venue}'
        capability_id=f'{provider_id}:market-data:{route_key}'
        if provider_router.policy.datasets.get(route_key)!=capability_id:
            raise ValueError('provider daily index dataset is not selected in routing policy')
        return dataset_publisher.index_daily_snapshot(provider_id,index_instrument_id,venue)

    @app.get('/internal/v1/backtest/data')
    def detailed_data():return [TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures').manifest()]

    @app.post('/internal/v1/paper/prepare')
    def prepare_order(value:PaperPrepare):
        events,rules=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures').load(value.snapshot)
        if value.sequence<1 or value.sequence>len(events):raise ValueError('advance fixture clock before placing an order')
        event=events[value.sequence-1]
        order=Order(id=value.id,instrument_id=event.instrument_id,side=value.side,order_type='LO',limit_price=value.limit_price,quantity=value.quantity,created_at=event.received_at)
        validate_order(order,rules,event.event_time.date())
        return order.model_dump(mode='json')|{'reserve_rate':rules.fee_rate}

    @app.post('/internal/v1/paper/evaluate')
    def evaluate_paper(value:PaperEvaluate):
        events,rules=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures').load(value.snapshot)
        if value.after<0 or value.after>=len(events):raise ValueError('fixture tape exhausted or invalid cursor')
        event=events[value.after];fills=[];bid=Decimal(event.bid_size or '0');ask=Decimal(event.ask_size or '0')
        for raw in value.orders:
            if raw['status']!='open':continue
            order=Order(id=raw['id'],instrument_id=raw['instrument_id'],side=raw['side'],order_type='LO',limit_price=raw['limit_price'],quantity=raw['quantity'],created_at=raw['created_at'])
            available=event.model_copy(update={'bid_size':str(bid),'ask_size':str(ask)})
            fill=quote_fill(order,available,rules,True,raw['remaining'])
            if fill:
                fills.append(fill)
                if fill.side=='buy':ask-=Decimal(fill.quantity)
                else:bid-=Decimal(fill.quantity)
        return {'event':event,'fills':fills}

    @app.get('/internal/v1/sources')
    def sources(): return gate.status()

    @app.get('/internal/v1/market/live-status')
    def live_status():
        return {'state':'unavailable','reason':'SSI streaming and replay capability not approved; no live transport started','source_state':gate.status(),'reconciliation_required':True}

    @app.post('/internal/v1/programs/inspect')
    def inspect(value:InspectRequest):return inspect_source(value.source,value.kind,value.selected)

    @app.post('/internal/v1/runner/start',status_code=202)
    def start_run(value:RunRequest):runs.start(value.model_dump());return {'id':value.id}

    @app.get('/internal/v1/runner/{identity}/events')
    def run_events(identity:str,after:int=0):
        if after<0:raise ValueError('invalid cursor')
        return runs.events(identity,after)

    @app.post('/internal/v1/runner/{identity}/stop',status_code=202)
    def stop_run(identity:str):runs.cancel(identity);return {'status':'stop_requested'}

    @app.get('/internal/v1/market/candles')
    def candles(instrument_id:str): return market.latest_fixture(instrument_id)

    @app.get('/internal/v1/quant/indicators')
    def indicator_list(): return INDICATORS

    @app.get('/internal/v1/quant/calculate')
    def quant(instrument_id:str,indicator:str='sma',period:int=14,benchmark_id:str|None=None,annualization:int|None=None):
        snapshot=market.latest_fixture(instrument_id)
        benchmark=market.latest_fixture(benchmark_id).candles if benchmark_id else None
        if snapshot.quality.gaps: raise ValueError('resolve snapshot gaps before computing continuous indicators')
        return calculate(indicator,snapshot.candles,period,benchmark,annualization)|{'snapshot_id':snapshot.snapshot_id,'quality':snapshot.quality.model_dump()}

    return app

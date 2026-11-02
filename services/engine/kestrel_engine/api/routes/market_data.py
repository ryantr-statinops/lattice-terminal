"""Market catalogue, snapshot, and provider ingestion endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter
from ..context import EngineServices
from ..schemas import SsiCatalogueIngest, SsiDailyIndexIngest, SsiDailyOhlcIngest, SsiIndexCatalogueIngest, SsiIndexComponentsIngest
from ...models import DatasetEnvelope

def build_market_router(services: EngineServices) -> APIRouter:
    router = APIRouter()
    market = services.market
    dataset_publisher = services.dataset_publisher
    gate = services.gate
    provider_router = services.provider_router
    @router.get('/internal/v1/market/instruments')
    def instruments(provider_id:str=''):
        if provider_id:
            return dataset_publisher.instrument_catalogue(provider_id)
        return market.instruments()

    @router.get('/internal/v1/market/snapshots')
    def snapshots(): return market.manifests()

    @router.get('/internal/v1/market/datasets')
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

    @router.post('/internal/v1/market/catalogues/ssi/hose-equity')
    def ingest_ssi_hose_equity_catalogue(value:SsiCatalogueIngest):
        return _ingest_ssi_equity_catalogue(value,'HOSE')

    @router.post('/internal/v1/market/catalogues/ssi/hnx-equity')
    def ingest_ssi_hnx_equity_catalogue(value:SsiCatalogueIngest):
        return _ingest_ssi_equity_catalogue(value,'HNX')

    @router.post('/internal/v1/market/catalogues/ssi/upcom-equity')
    def ingest_ssi_upcom_equity_catalogue(value:SsiCatalogueIngest):
        return _ingest_ssi_equity_catalogue(value,'UPCOM')

    @router.post('/internal/v1/market/catalogues/ssi/hose-covered-warrants')
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

    @router.post('/internal/v1/market/catalogues/ssi/der-futures')
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

    @router.post('/internal/v1/market/catalogues/ssi/hose-etfs')
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

    @router.post('/internal/v1/market/catalogues/ssi/hnxbond-bonds')
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

    @router.post('/internal/v1/market/catalogues/ssi/hose-indices')
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

    @router.post('/internal/v1/market/catalogues/ssi/hnx-indices')
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

    @router.post('/internal/v1/market/index-components/ssi/hose')
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

    @router.post('/internal/v1/market/index-series/ssi/hose/daily')
    def ingest_ssi_hose_daily_index(value:SsiDailyIndexIngest):
        return _ingest_ssi_daily_index(value,'HOSE')

    @router.post('/internal/v1/market/index-series/ssi/hnx/daily')
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

    @router.post('/internal/v1/market/candles/ssi/hose-equity/daily')
    def ingest_ssi_hose_equity_daily(value:SsiDailyOhlcIngest):
        return _ingest_ssi_equity_daily(value,'HOSE')

    @router.post('/internal/v1/market/candles/ssi/hnx-equity/daily')
    def ingest_ssi_hnx_equity_daily(value:SsiDailyOhlcIngest):
        return _ingest_ssi_equity_daily(value,'HNX')

    @router.get('/internal/v1/market/provider-candles')
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

    @router.get('/internal/v1/market/provider-index-constituents')
    def provider_index_constituents(provider_id:str,index_instrument_id:str):
        route_key='indices.constituents:index:HOSE'
        capability_id=f'{provider_id}:market-data:{route_key}'
        if provider_router.policy.datasets.get(route_key)!=capability_id:
            raise ValueError('provider index constituent dataset is not selected in routing policy')
        return dataset_publisher.index_constituent_snapshot(provider_id,index_instrument_id)

    @router.get('/internal/v1/market/provider-index-daily')
    def provider_index_daily(provider_id:str,index_instrument_id:str,venue:str):
        route_key=f'indices.daily:index:{venue}'
        capability_id=f'{provider_id}:market-data:{route_key}'
        if provider_router.policy.datasets.get(route_key)!=capability_id:
            raise ValueError('provider daily index dataset is not selected in routing policy')
        return dataset_publisher.index_daily_snapshot(provider_id,index_instrument_id,venue)

    return router

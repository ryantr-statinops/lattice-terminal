import hashlib
import json
from pathlib import Path
from .stream import MarketEvent
from .execution import FillModel,RulePack

class TapeRepository:
    def __init__(self,fixtures:Path):self.path=fixtures/'detailed-events.json'
    def manifest(self):
        raw=self.path.read_bytes();value=json.loads(raw)
        if value.get('is_synthetic') is not True or value.get('granularity')!='quote-events':raise ValueError('detailed synthetic tape required')
        return {'snapshot_id':hashlib.sha256(raw).hexdigest(),'source_id':'SYNTHETIC-FIXTURE','is_synthetic':True,'granularity':'quote-events','event_count':len(value['events']),'rule_pack':value['rules']['id'],'fill_models':[model['id'] for model in value.get('fill_models',[])],'start':value['events'][0]['event_time'],'end':value['events'][-1]['event_time']}
    def load(self,key):
        if key!=self.manifest()['snapshot_id']:raise ValueError('detailed event snapshot unavailable; OHLC is not accepted for fills')
        value=json.loads(self.path.read_text());events=[MarketEvent.model_validate(v) for v in value['events']]
        if any(not v.is_synthetic for v in events):raise ValueError('fixture/production boundary mismatch')
        if len({v.id for v in events})!=len(events):raise ValueError('duplicate event id')
        if events!=sorted(events,key=lambda v:(v.event_time,v.sequence)):raise ValueError('event tape out of order')
        return events,RulePack.model_validate(value['rules'])
    def fill_models(self,key):
        if key!=self.manifest()['snapshot_id']:raise ValueError('detailed event snapshot unavailable; OHLC is not accepted for fills')
        value=json.loads(self.path.read_text())
        return [FillModel.model_validate(model) for model in value.get('fill_models',[])]

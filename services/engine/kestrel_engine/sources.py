"""Independent evidence flags; no flag or probe automatically grants rights."""
from datetime import datetime,timezone
from pathlib import Path
from pydantic import AwareDatetime,Field
from .models import Record

CAPABILITIES=['SSI-FC-DATA-REST','SSI-FC-DATA-STREAM']
class SourceBlocked(ValueError):pass
class Scope(Record):
    endpoints:list[str]=Field(min_length=1)
    purposes:list[str]=Field(min_length=1)
    fields:list[str]=Field(min_length=1)
    request_limit:int=Field(gt=0)
    timeout_seconds:int=Field(gt=0,le=120)
    retention_allowed:bool=False
    export_allowed:bool=False
    terms_reference:str=Field(min_length=1)
    entitlement_reference:str=Field(min_length=1)
    expires_at:AwareDatetime

class Evidence(Record):
    id:str
    documented:bool=True
    access_tested:bool=False
    rights_confirmed:bool=False
    approved:bool=False
    access_reference:str|None=None
    rights_reference:str|None=None
    approval_reference:str|None=None
    scope:Scope|None=None
    probe_authorized:bool=False
    probe_reference:str|None=None
    probe_scope:Scope|None=None

class SourceGate:
    def __init__(self,root:Path):self.path=root/'source-policy.json'
    def records(self):
        if not self.path.exists():return {v:Evidence(id=v) for v in CAPABILITIES}
        import json
        values=json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(values,list):raise SourceBlocked('invalid source policy; access disabled')
        records={v.id:v for v in map(Evidence.model_validate,values)}
        for key in CAPABILITIES:records.setdefault(key,Evidence(id=key))
        return records
    def authorize(self,capability:str,purpose:str,endpoint:str,probe:bool=False)->Scope:
        record=self.records().get(capability)
        if not record:raise SourceBlocked('capability not registered')
        scope=record.probe_scope if probe else record.scope
        if probe:
            if not record.probe_authorized or not record.probe_reference:raise SourceBlocked('scoped probe authorization required')
        elif not all([record.documented,record.access_tested,record.rights_confirmed,record.approved,record.access_reference,record.rights_reference,record.approval_reference]):
            raise SourceBlocked('production access/rights/approval evidence incomplete')
        if not scope or not scope.terms_reference or not scope.entitlement_reference:raise SourceBlocked('terms and entitlement scope required')
        if datetime.now(timezone.utc)>=scope.expires_at:raise SourceBlocked('source scope expired')
        if purpose not in scope.purposes or endpoint not in scope.endpoints:raise SourceBlocked('purpose/endpoint outside approved scope')
        if purpose in ['store','backtest'] and not scope.retention_allowed:raise SourceBlocked('retention not permitted')
        if purpose=='export' and not scope.export_allowed:raise SourceBlocked('export not permitted')
        return scope
    def status(self):
        try:records=self.records()
        except Exception:return [{'id':v,'documented':True,'access_tested':False,'rights_confirmed':False,'approved':False,'operating_state':'fixture-only','reason':'invalid source policy; access disabled'} for v in CAPABILITIES]
        result=[]
        for record in records.values():
            state='fixture-only';reason='Account entitlement, rights and access evidence not verified'
            scope=record.scope
            if all([record.documented,record.access_tested,record.rights_confirmed,record.approved,record.access_reference,record.rights_reference,record.approval_reference]) and scope and scope.expires_at>datetime.now(timezone.utc):state='approved';reason='Only exact approved endpoints/purposes/fields may be used'
            elif record.probe_authorized and record.probe_reference and record.probe_scope and record.probe_scope.expires_at>datetime.now(timezone.utc):state='scoped-probe';reason='Probe only; no product serving or implicit retention'
            result.append({'id':record.id,'documented':record.documented,'access_tested':record.access_tested,'rights_confirmed':record.rights_confirmed,'approved':record.approved,'operating_state':state,'reason':reason})
        return result

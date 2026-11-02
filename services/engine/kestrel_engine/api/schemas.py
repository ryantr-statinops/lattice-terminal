"""Internal engine request models."""
from datetime import date
from typing import Any
from ..models import Record

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

"""Per-feed reconciliation state, independent of browser lifetime."""
from collections import deque
from datetime import datetime,timedelta
from pydantic import AwareDatetime,Field
from .models import Record,decimal_text

class MarketEvent(Record):
    id:str
    instrument_id:str
    feed:str
    sequence:int=Field(ge=0)
    event_time:AwareDatetime
    received_at:AwareDatetime
    source_id:str
    is_synthetic:bool=False
    kind:str
    session:str
    trading_status:str
    bid:str|None=None
    ask:str|None=None
    bid_size:str|None=None
    ask_size:str|None=None
    price:str|None=None
    size:str|None=None

class Reconciler:
    def __init__(self,max_age:timedelta):
        self.max_age=max_age;self.state='unavailable';self.reason='not_reconciled';self.sequence=None;self.last_time=None
        self.ids=set();self.recent=deque()
    def reconcile(self,cutoff:datetime,sequence:int):
        if cutoff.tzinfo is None:raise ValueError('timezone required')
        self.last_time=cutoff;self.sequence=sequence;self.state='ready';self.reason='reconciled'
    def disconnect(self):self.state='reconnecting';self.reason='requires_backfill_and_reconciliation'
    def apply(self,event:MarketEvent)->bool:
        if event.id in self.ids:return False
        if self.state!='ready':return False
        if self.sequence is None or event.sequence!=self.sequence+1:
            self.state='gap';self.reason='sequence_gap_or_reorder';return False
        if self.last_time is not None and event.event_time<self.last_time:
            self.state='gap';self.reason='out_of_order_timestamp';return False
        age=event.received_at-event.event_time
        if age<timedelta(0) or age>self.max_age:
            self.state='stale';self.reason='timestamp_or_freshness_unknown';return False
        self.sequence=event.sequence;self.last_time=event.event_time
        self.ids.add(event.id);self.recent.append(event.id)
        if len(self.recent)>10000:self.ids.discard(self.recent.popleft())
        return True
    def freshness(self,now:datetime)->bool:
        if self.last_time is None or now-self.last_time>self.max_age:
            self.state='stale';self.reason='no_recent_event';return False
        return self.state=='ready'

class Subscriptions:
    """Multiplex consumers; unsubscribe cannot tear down another consumer's feed."""
    def __init__(self):self.consumers={}
    def set(self,consumer:str,keys:set[tuple[str,str]]):self.consumers[consumer]=set(keys)
    def remove(self,consumer:str):self.consumers.pop(consumer,None)
    def required(self):return set().union(*self.consumers.values()) if self.consumers else set()

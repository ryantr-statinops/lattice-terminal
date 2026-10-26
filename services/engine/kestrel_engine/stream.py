"""Per-feed reconciliation state, independent of browser lifetime."""
from __future__ import annotations

from collections import deque
from datetime import datetime,timedelta
from pydantic import AwareDatetime,Field,field_validator
from threading import RLock
from typing import Callable,Protocol
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
    @field_validator('bid','ask','bid_size','ask_size','price','size')
    @classmethod
    def numbers(cls,value):return decimal_text(value) if value is not None else None

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

class SubscriptionConnection(Protocol):
    def set_instruments(self, instrument_ids: frozenset[str]) -> None: ...
    def close(self) -> None: ...


class Subscriptions:
    """Share one provider connection across consumers and union their instruments."""
    def __init__(self, connector: Callable[[str], SubscriptionConnection] | None = None):
        self.consumers: dict[str, set[tuple[str, str]]] = {}
        self.connector = connector
        self._connections: dict[str, SubscriptionConnection] = {}
        self._lock = RLock()

    @staticmethod
    def _desired(consumers: dict[str, set[tuple[str, str]]]) -> dict[str, frozenset[str]]:
        result: dict[str, set[str]] = {}
        for keys in consumers.values():
            for feed, instrument_id in keys:
                result.setdefault(feed, set()).add(instrument_id)
        return {feed: frozenset(instruments) for feed, instruments in result.items()}

    def set(self, consumer: str, keys: set[tuple[str, str]]) -> None:
        if not consumer.strip():
            raise ValueError('subscription consumer is required')
        normalized = set(keys)
        if any(not feed.strip() or not instrument_id.strip() for feed, instrument_id in normalized):
            raise ValueError('subscription feed and instrument are required')
        with self._lock:
            candidate = dict(self.consumers)
            candidate[consumer] = normalized
            self._apply(candidate)

    def remove(self, consumer: str) -> None:
        with self._lock:
            candidate = dict(self.consumers)
            candidate.pop(consumer, None)
            self._apply(candidate)

    def required(self) -> set[tuple[str, str]]:
        with self._lock:
            return set().union(*self.consumers.values()) if self.consumers else set()

    def close(self) -> None:
        with self._lock:
            connections, self._connections = self._connections, {}
            self.consumers = {}
            for connection in connections.values():
                connection.close()

    def _apply(self, candidate: dict[str, set[tuple[str, str]]]) -> None:
        if self.connector is None:
            self.consumers = candidate
            return
        old_desired = self._desired(self.consumers)
        new_desired = self._desired(candidate)
        staged: dict[str, SubscriptionConnection] = {}
        changed: list[tuple[SubscriptionConnection, frozenset[str]]] = []
        try:
            for feed, instruments in sorted(new_desired.items()):
                connection = self._connections.get(feed)
                if connection is None:
                    connection = self.connector(feed)
                    staged[feed] = connection
                    connection.set_instruments(instruments)
                elif instruments != old_desired.get(feed, frozenset()):
                    changed.append((connection, old_desired[feed]))
                    connection.set_instruments(instruments)
        except Exception:
            for connection, previous in reversed(changed):
                try:
                    connection.set_instruments(previous)
                except Exception:
                    connection.close()
                    self._connections = {key: value for key, value in self._connections.items() if value is not connection}
            for connection in staged.values():
                connection.close()
            raise

        active = {feed: self._connections[feed] for feed in new_desired if feed in self._connections}
        active.update(staged)
        for feed, connection in self._connections.items():
            if feed not in new_desired:
                connection.close()
        self._connections = active
        self.consumers = candidate

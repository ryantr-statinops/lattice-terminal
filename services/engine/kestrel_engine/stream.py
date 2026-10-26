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
    def __init__(self, connector: Callable[[str], SubscriptionConnection] | None = None, *,
                 event_handler: Callable[[MarketEvent], None] | None = None, require_event_handler: bool = False):
        self.consumers: dict[str, set[tuple[str, str]]] = {}
        self.connector = connector
        self.event_handler = event_handler
        self.require_event_handler = require_event_handler
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
                    bind_event_handler = getattr(connection, 'set_event_handler', None)
                    if self.event_handler is not None:
                        if not callable(bind_event_handler) and self.require_event_handler:
                            raise TypeError('live provider connection must support event delivery')
                        if callable(bind_event_handler):
                            bind_event_handler(self.event_handler)
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


class ReconciledLiveFeeds:
    """Route provider events to subscribed consumers only after feed reconciliation."""
    def __init__(self, connector: Callable[[str], SubscriptionConnection] | None = None,
                 max_age: timedelta = timedelta(seconds=5)):
        if max_age <= timedelta(0):
            raise ValueError('live feed maximum age must be positive')
        self.max_age = max_age
        self._reconcilers: dict[str, Reconciler] = {}
        self._consumers: dict[str, tuple[set[tuple[str, str]], Callable[[MarketEvent], None]]] = {}
        self._recovering: set[str] = set()
        self._lock = RLock()
        self.subscriptions = Subscriptions(connector, event_handler=self.publish, require_event_handler=True)

    def set(self, consumer: str, keys: set[tuple[str, str]], handler: Callable[[MarketEvent], None]) -> None:
        if not callable(handler):
            raise ValueError('live event handler is required')
        normalized = set(keys)
        with self._lock:
            previous = self._consumers.get(consumer)
            self._consumers[consumer] = (normalized, handler)
            try:
                self.subscriptions.set(consumer, normalized)
            except Exception:
                if previous is None:
                    self._consumers.pop(consumer, None)
                else:
                    self._consumers[consumer] = previous
                raise

    def remove(self, consumer: str) -> None:
        with self._lock:
            self.subscriptions.remove(consumer)
            self._consumers.pop(consumer, None)

    def reconcile(self, feed: str, cutoff: datetime, sequence: int) -> None:
        if not feed.strip() or sequence < 0:
            raise ValueError('feed and non-negative sequence are required')
        with self._lock:
            if feed in self._recovering:
                raise RuntimeError('feed reconciliation is owned by an active backfill')
            self._reconcilers.setdefault(feed, Reconciler(self.max_age)).reconcile(cutoff, sequence)

    def disconnect(self, feed: str) -> None:
        with self._lock:
            reconciler = self._reconcilers.get(feed)
            if reconciler is not None:
                reconciler.disconnect()

    def publish(self, event: MarketEvent) -> bool:
        with self._lock:
            reconciler = self._reconcilers.get(event.feed)
            if reconciler is None or not reconciler.apply(event):
                return False
            handlers = [
                handler for keys, handler in self._consumers.values()
                if (event.feed, event.instrument_id) in keys
            ]
        for handler in handlers:
            handler(event)
        return True

    def backfill(self, feed: str, through_sequence: int,
                 fetch: Callable[[str, int, int], list[MarketEvent]],
                 persist: Callable[[list[MarketEvent]], None]) -> int:
        """Persist a complete sequence gap before reopening live event delivery."""
        with self._lock:
            reconciler = self._reconcilers.get(feed)
            if reconciler is None or reconciler.sequence is None or reconciler.last_time is None:
                raise ValueError('live feed has no reconciliation point to backfill from')
            if reconciler.state == 'ready':
                raise ValueError('live feed must be paused before gap backfill')
            if feed in self._recovering:
                raise RuntimeError('live feed already has a backfill in progress')
            previous_sequence = reconciler.sequence
            previous_time = reconciler.last_time
            if through_sequence < previous_sequence:
                raise ValueError('backfill watermark precedes the last accepted event')
            self._recovering.add(feed)

        try:
            events = fetch(feed, previous_sequence, through_sequence)
            expected_sequence = previous_sequence
            last_time = previous_time
            for event in events:
                expected_sequence += 1
                if event.feed != feed or event.sequence != expected_sequence:
                    raise ValueError('backfill events must match the feed and contain no sequence gaps')
                if event.event_time < last_time or event.received_at < event.event_time:
                    raise ValueError('backfill event time must be ordered and available')
                last_time = event.event_time
            if expected_sequence != through_sequence:
                raise ValueError('backfill does not cover the requested sequence watermark')

            if events:
                persist(events)

            with self._lock:
                current = self._reconcilers.get(feed)
                if current is not reconciler or current.sequence != previous_sequence or current.state == 'ready':
                    raise RuntimeError('live feed changed while its gap was being backfilled')
                current.reconcile(last_time, through_sequence)
            return len(events)
        finally:
            with self._lock:
                self._recovering.discard(feed)

    def status(self, feed: str) -> dict[str, object]:
        with self._lock:
            reconciler = self._reconcilers.get(feed)
            if reconciler is None:
                return {'feed': feed, 'state': 'unavailable', 'reason': 'not_reconciled', 'sequence': None}
            return {'feed': feed, 'state': reconciler.state, 'reason': reconciler.reason, 'sequence': reconciler.sequence}

    def close(self) -> None:
        with self._lock:
            self._consumers.clear()
            self._reconcilers.clear()
            self.subscriptions.close()

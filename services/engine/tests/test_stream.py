from datetime import datetime,timedelta,timezone
from kestrel_engine.stream import MarketEvent,Reconciler,Subscriptions

def event(seq=1):
    now=datetime(2026,10,1,2,tzinfo=timezone.utc)
    return MarketEvent(id=f'e{seq}',instrument_id='SYN',feed='quote',sequence=seq,event_time=now,received_at=now,source_id='SYNTHETIC-FIXTURE',is_synthetic=True,kind='quote',session='synthetic-continuous',trading_status='trading')

def test_gap_duplicate_reconnect_and_stale_block_delivery():
    value=event();state=Reconciler(timedelta(seconds=5))
    assert not state.apply(value)
    state.reconcile(value.event_time,0)
    assert state.apply(value)
    assert not state.apply(value)
    assert not state.apply(event(3)) and state.state=='gap'
    state.reconcile(value.event_time,2);state.disconnect()
    assert not state.apply(event(3))
    state.reconcile(value.event_time,0)
    assert not state.apply(value.model_copy(update={'received_at':value.event_time+timedelta(seconds=6)}))

def test_subscription_consumers_are_independent():
    s=Subscriptions();s.set('manual',{('X','SYN')});s.set('strategy',{('X','SYN'),('B','SYN')});s.remove('manual')
    assert s.required()=={('X','SYN'),('B','SYN')}

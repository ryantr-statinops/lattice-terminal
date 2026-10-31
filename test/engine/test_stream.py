from datetime import datetime,timedelta,timezone
from kestrel_engine.stream import MarketEvent,ReconciledLiveFeeds,Reconciler,Subscriptions

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

def test_subscription_manager_shares_provider_connection_and_unions_consumers():
    class Connection:
        def __init__(self):self.updates=[];self.closed=False
        def set_instruments(self,instruments):self.updates.append(instruments)
        def close(self):self.closed=True
    opened=[]
    def connect(feed):
        connection=Connection();opened.append((feed,connection));return connection

    manager=Subscriptions(connect)
    manager.set('manual',{('ssi-stream','AAA'),('ssi-stream','BBB')})
    manager.set('strategy',{('ssi-stream','BBB'),('dnse-stream','CCC')})

    assert [feed for feed,_ in opened]==['ssi-stream','dnse-stream']
    assert opened[0][1].updates==[frozenset({'AAA','BBB'})]
    assert opened[1][1].updates==[frozenset({'CCC'})]
    manager.remove('manual')
    assert not opened[0][1].closed and opened[0][1].updates[-1]==frozenset({'BBB'})
    manager.remove('strategy')
    assert all(connection.closed for _,connection in opened)

def test_subscription_manager_rolls_back_consumer_state_when_provider_update_fails():
    class Connection:
        def __init__(self):self.current=frozenset();self.fail_next=False
        def set_instruments(self,instruments):
            if self.fail_next:
                self.fail_next=False
                raise RuntimeError('subscription update failed')
            self.current=instruments
        def close(self):pass
    connection=Connection();manager=Subscriptions(lambda _:connection)
    manager.set('strategy',{('ssi-stream','AAA')})
    connection.fail_next=True

    import pytest
    with pytest.raises(RuntimeError,match='subscription update failed'):
        manager.set('manual',{('ssi-stream','BBB')})

    assert manager.required()=={('ssi-stream','AAA')}
    assert connection.current==frozenset({'AAA'})

def test_live_events_reach_consumers_only_after_reconciliation():
    class Connection:
        def set_instruments(self,instruments):self.instruments=instruments
        def set_event_handler(self,handler):self.on_event=handler
        def close(self):pass

    connections={}
    def connect(feed):
        connections[feed]=Connection()
        return connections[feed]

    runtime=ReconciledLiveFeeds(connect,max_age=timedelta(seconds=5))
    received=[]
    runtime.set('strategy',{('ssi-quote','SYN'),('ssi-quote','OTHER')},received.append)
    connection=connections['ssi-quote']
    value=event().model_copy(update={'feed':'ssi-quote','is_synthetic':False})

    assert not connection.on_event(value)
    runtime.reconcile('ssi-quote',value.event_time,0)
    assert connection.on_event(value)
    assert not connection.on_event(value)
    assert received==[value]
    assert runtime.status('ssi-quote')=={'feed':'ssi-quote','state':'ready','reason':'reconciled','sequence':1}

    assert not connection.on_event(value.model_copy(update={'id':'gap','sequence':3}))
    assert runtime.status('ssi-quote')['state']=='gap'
    runtime.disconnect('ssi-quote')
    assert runtime.status('ssi-quote')['state']=='reconnecting'
    runtime.close()

def test_live_runtime_requires_provider_event_delivery_contract():
    class Connection:
        def set_instruments(self,instruments):pass
        def close(self):pass

    runtime=ReconciledLiveFeeds(lambda _:Connection())
    import pytest
    with pytest.raises(TypeError,match='must support event delivery'):
        runtime.set('manual',{('provider-feed','SYN')},lambda _:None)
    assert runtime.subscriptions.required()==set()
    assert 'manual' not in runtime._consumers

def test_live_gap_backfill_persists_contiguous_history_before_resuming():
    class Connection:
        def set_instruments(self,instruments):pass
        def set_event_handler(self,handler):self.on_event=handler
        def close(self):pass

    connection=Connection();runtime=ReconciledLiveFeeds(lambda _:connection,max_age=timedelta(seconds=5))
    received=[];persisted=[]
    runtime.set('strategy',{('quote','SYN')},received.append)
    first=event(1).model_copy(update={'feed':'quote'})
    runtime.reconcile('quote',first.event_time,0)
    assert connection.on_event(first)
    gap=event(4).model_copy(update={'feed':'quote'})
    assert not connection.on_event(gap)

    def fetch(feed,after,through):
        assert (feed,after,through)==('quote',1,3)
        return [event(seq).model_copy(update={'feed':'quote'}) for seq in (2,3)]

    assert runtime.backfill('quote',3,fetch,persisted.extend)==2
    assert [value.sequence for value in persisted]==[2,3]
    assert [value.sequence for value in received]==[1]
    assert runtime.status('quote')['state']=='ready'
    assert connection.on_event(gap)
    assert [value.sequence for value in received]==[1,4]

def test_live_gap_backfill_rejects_missing_or_unpersisted_range():
    class Connection:
        def set_instruments(self,instruments):pass
        def set_event_handler(self,handler):self.on_event=handler
        def close(self):pass

    connection=Connection();runtime=ReconciledLiveFeeds(lambda _:connection)
    first=event(1).model_copy(update={'feed':'quote'})
    runtime.set('manual',{('quote','SYN')},lambda _:None)
    runtime.reconcile('quote',first.event_time,0)
    connection.on_event(first)
    assert not connection.on_event(event(3).model_copy(update={'feed':'quote'}))
    stored=[]

    import pytest
    with pytest.raises(ValueError,match='sequence gaps'):
        runtime.backfill('quote',2,lambda *_:[event(2).model_copy(update={'feed':'other'}),event(3).model_copy(update={'feed':'quote'})],stored.extend)
    assert stored==[]
    assert runtime.status('quote')['state']=='gap'

    def fail_to_persist(_):raise RuntimeError('storage unavailable')
    with pytest.raises(RuntimeError,match='storage unavailable'):
        runtime.backfill('quote',3,lambda *_:[event(seq).model_copy(update={'feed':'quote'}) for seq in (2,3)],fail_to_persist)
    assert runtime.status('quote')['state']=='gap'

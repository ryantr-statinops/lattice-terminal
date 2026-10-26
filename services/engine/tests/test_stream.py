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

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import pytest
from kestrel_engine.strategy import execute_program
from kestrel_engine.tapes import TapeRepository

def test_strategy_contract_emits_paper_events_and_is_not_backtest(monkeypatch, repository_paths):
    repo=TapeRepository(repository_paths['fixtures']);output=[]
    base=SimpleNamespace(params={'paper_source':'fixture-replay','allocation_id':'a','allocation_cash':'100000','event_snapshot':repo.manifest()['snapshot_id'],'allocation_positions':{}},run_id='run',emit=lambda kind,payload:output.append((kind,payload)),log=lambda message:None)
    monkeypatch.setattr('kestrel_engine.strategy.time.sleep',lambda value:None)
    called=[]
    execute_program({'on_event':lambda ctx,event:called.append(event.sequence) or []},base)
    assert len(called)==80
    assert output[-1][0]=='paper_session'
    base.params['paper_source']='ssi-live'
    with pytest.raises(ValueError,match='SSI live'):execute_program({'on_event':lambda ctx,event:[]},base)

def test_strategy_paper_mutations_share_one_market_step_event(monkeypatch, repository_paths):
    repo=TapeRepository(repository_paths['fixtures']);output=[]
    base=SimpleNamespace(params={'paper_source':'fixture-replay','allocation_id':'a','allocation_cash':'100000','event_snapshot':repo.manifest()['snapshot_id'],'allocation_positions':{}},run_id='run-step',emit=lambda kind,payload:output.append((kind,payload)),log=lambda message:None)
    monkeypatch.setattr('kestrel_engine.strategy.time.sleep',lambda value:None)
    def on_event(context,event):
        if event.sequence==1:return [{'side':'buy','limit_price':'10010','quantity':'1'}]
        return []
    execute_program({'on_event':on_event},base)
    steps=[payload for kind,payload in output if kind=='paper_step']
    assert len(steps)==80
    assert steps[0]['after_sequence']==0 and steps[0]['sequence']==1
    assert steps[0]['mutations'][0]['type']=='paper_order'
    assert not any(kind in {'paper_order','paper_fill','paper_cursor'} for kind,_ in output)


def test_strategy_context_signal_is_independent_from_paper_order_intents(monkeypatch, repository_paths):
    repo=TapeRepository(repository_paths['fixtures']);output=[]
    base=SimpleNamespace(params={
        'paper_source':'fixture-replay','allocation_id':'a','allocation_cash':'100000',
        'event_snapshot':repo.manifest()['snapshot_id'],'allocation_positions':{},'strategy_id':'breakout',
    },run_id='run-signal',emit=lambda kind,payload:output.append((kind,payload)),log=lambda message:None)
    monkeypatch.setattr('kestrel_engine.strategy.time.sleep',lambda value:None)

    def on_event(context,event):
        if event.sequence==1:
            signal=context.signal(action='buy',reason='breakout confirmed',logical_key='breakout:HPG')
            duplicate=context.signal(action='buy',reason='breakout confirmed',logical_key='breakout:HPG')
            assert duplicate.id==signal.id
            assert signal.expires_at-signal.event_time==timedelta(minutes=5)
        return []

    execute_program({'on_event':on_event},base)
    signals=[payload for kind,payload in output if kind=='signal']
    assert len(signals)==1
    assert signals[0]['strategy_id']=='breakout'
    assert signals[0]['source']=='replay'
    assert signals[0]['instrument_id']=='HOSE:REGULAR:equity:SYN01'
    assert not any(kind=='paper_order' for kind,_ in output)

def test_signal_only_strategy_replays_without_an_allocation(monkeypatch, repository_paths):
    repo=TapeRepository(repository_paths['fixtures']);output=[]
    base=SimpleNamespace(params={
        'strategy_mode':'signal_only','paper_source':'fixture-replay',
        'event_snapshot':repo.manifest()['snapshot_id'],'strategy_id':'watch-only',
    },run_id='run-signal-only',emit=lambda kind,payload:output.append((kind,payload)),log=lambda message:None)
    monkeypatch.setattr('kestrel_engine.strategy.time.sleep',lambda value:None)
    def on_event(context,event):
        if event.sequence==1:
            context.signal(action='custom',custom_action='watch',reason='condition observed',logical_key='watch:SYN01')
        return []
    execute_program({'on_event':on_event},base)
    assert [kind for kind,_ in output]==['signal']
    assert output[0][1]['strategy_id']=='watch-only'
    assert output[0][1]['source']=='replay'

def test_signal_only_strategy_rejects_order_intents(monkeypatch, repository_paths):
    repo=TapeRepository(repository_paths['fixtures']);output=[]
    base=SimpleNamespace(params={
        'strategy_mode':'signal_only','paper_source':'fixture-replay',
        'event_snapshot':repo.manifest()['snapshot_id'],
    },run_id='run-signal-order',emit=lambda kind,payload:output.append((kind,payload)),log=lambda message:None)
    monkeypatch.setattr('kestrel_engine.strategy.time.sleep',lambda value:None)
    with pytest.raises(ValueError,match='cannot emit paper order intents'):
        execute_program({'on_event':lambda context,event:[{'side':'buy','limit_price':'10000','quantity':'1'}]},base)
    assert not any(kind.startswith('paper_') for kind,_ in output)

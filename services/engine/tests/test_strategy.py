from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import pytest
from kestrel_engine.strategy import execute_program
from kestrel_engine.tapes import TapeRepository

def test_strategy_contract_emits_paper_events_and_is_not_backtest(monkeypatch):
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');output=[]
    base=SimpleNamespace(params={'paper_source':'fixture-replay','allocation_id':'a','allocation_cash':'100000','event_snapshot':repo.manifest()['snapshot_id'],'allocation_positions':{}},run_id='run',emit=lambda kind,payload:output.append((kind,payload)),log=lambda message:None)
    monkeypatch.setattr('kestrel_engine.strategy.time.sleep',lambda value:None)
    called=[]
    execute_program({'on_event':lambda ctx,event:called.append(event.sequence) or []},base)
    assert len(called)==80
    assert output[-1][0]=='paper_session'
    base.params['paper_source']='ssi-live'
    with pytest.raises(ValueError,match='SSI live'):execute_program({'on_event':lambda ctx,event:[]},base)


def test_strategy_context_signal_is_independent_from_paper_order_intents(monkeypatch):
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');output=[]
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

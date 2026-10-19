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

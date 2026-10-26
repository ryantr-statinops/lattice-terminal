from pathlib import Path
from decimal import Decimal
import pytest
from kestrel_engine.tapes import TapeRepository
from kestrel_engine.backtest import Replay

def test_backtest_history_only_and_conserved_cash():
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');events,rules=repo.load(repo.manifest()['snapshot_id'])
    seen=[]
    def decide(view,event):
        seen.append(len(view.history))
        assert all(v.event_time<=event.event_time for v in view.history)
        return [{'side':'buy','limit_price':'11000','quantity':'2'}] if len(view.history)==1 else []
    replay=Replay(events,rules,'100000',fill_models=repo.fill_models(repo.manifest()['snapshot_id']))
    rules.settlement_calendar.clear()
    report=replay.run(decide)
    assert seen==list(range(1,len(events)+1))
    assert report['simulated_fill_count']==1
    fill=report['fills'][0]
    assert fill['event_id']==events[1].id
    assert Decimal(report['final_nav'])==Decimal('100000')-Decimal(fill['price'])*2+(Decimal(events[-1].bid)+Decimal(events[-1].ask))
    assert report['sharpe'] is None
    assert report['calendar_id']==f'{rules.id}:calendar'
    assert len(report['calendar_snapshot_id'])==64
    assert report['fee_tax_schedule_id']==f'{rules.id}:costs'
    assert len(report['fee_tax_schedule_snapshot_id'])==64
    assert report['fill_model_ids']==['SYNTHETIC-HOSE-REGULAR-EQUITY-LO-CONTINUOUS-V1']

def test_daily_snapshot_not_accepted_as_detailed_tape():
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures')
    with pytest.raises(ValueError,match='OHLC'):repo.load('not-a-detailed-snapshot')

def test_replay_blocks_when_no_fill_model_covers_dataset():
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');events,rules=repo.load(repo.manifest()['snapshot_id'])
    with pytest.raises(ValueError,match='no fill model'):
        Replay(events,rules,'100000').run(lambda view,event:[])

def test_replay_blocks_when_quote_liquidity_is_incomplete():
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');events,rules=repo.load(repo.manifest()['snapshot_id'])
    events[0]=events[0].model_copy(update={'ask_size':None})
    with pytest.raises(ValueError,match='liquidity fields are incomplete'):
        Replay(events,rules,'100000',fill_models=repo.fill_models(repo.manifest()['snapshot_id'])).run(lambda view,event:[])

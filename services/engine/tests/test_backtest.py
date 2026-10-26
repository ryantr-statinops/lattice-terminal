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
    replay=Replay(events,rules,'100000')
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

def test_daily_snapshot_not_accepted_as_detailed_tape():
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures')
    with pytest.raises(ValueError,match='OHLC'):repo.load('not-a-detailed-snapshot')

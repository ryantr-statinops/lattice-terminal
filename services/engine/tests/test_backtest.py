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
    replay=Replay(events,rules,'100000',fill_models=repo.fill_models(repo.manifest()['snapshot_id']),data_snapshot_id=repo.manifest()['snapshot_id'])
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
    assert report['data_snapshot_id']==repo.manifest()['snapshot_id']
    assert len(report['rule_pack_snapshot_id'])==64
    assert len(report['fill_model_snapshot_id'])==64
    assert report['fill_assumptions']['queue_position']=='not reconstructed'

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

def test_backtest_context_pins_code_and_dependency_provenance():
    from kestrel_engine.backtest import BacktestContext
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');manifest=repo.manifest()
    class Base:
        run_id='backtest-run'
        params={'train_start':'2026-10-01T00:00:00+00:00','train_end':'2026-10-01T23:59:00+00:00','test_start':'2026-10-02T00:00:00+00:00','test_end':'2026-10-02T23:59:00+00:00','stage':'train','capital':'100000','event_snapshot':manifest['snapshot_id']}
        code_snapshot_id='a'*64
        engine_sha256='b'*64
        dependency_lock_sha256='c'*64
        def log(self,message):pass
        def table(self,*args):pass
        def chart(self,*args):pass
    context=BacktestContext(Base());context.replay(lambda view,event:[])
    assert context._report['code_snapshot_id']=='a'*64
    assert context._report['engine_sha256']=='b'*64
    assert context._report['dependency_lock_sha256']=='c'*64
    assert context._report['data_source_id']=='SYNTHETIC-FIXTURE'

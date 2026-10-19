"""Live-style callback contract; cannot run Backtest programs."""
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from .paper import PaperSession
from .sources import SourceBlocked
from .stream import Reconciler
from .tapes import TapeRepository

class StrategyContext:
    def __init__(self,base,session):self.params=base.params;self._base=base;self._session=session
    def log(self,message):self._base.log(message)
    @property
    def portfolio(self):return {'cash':str(self._session.cash),'positions':{k:str(v) for k,v in self._session.positions.items()}}

def execute_program(program,base):
    params=base.params
    if params.get('paper_source')!='fixture-replay':raise SourceBlocked('SSI live paper feed, rights and rule validation remain unavailable')
    allocation=params.get('allocation_id')
    if not allocation:raise ValueError('choose a strategy allocation')
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');events,rules=repo.load(params['event_snapshot'])
    after=int(params.get('after_sequence',0));events=[v for v in events if v.sequence>after]
    if not events:raise ValueError('fixture tape exhausted; existing positions remain held until eligible future data is available')
    session=PaperSession(params['allocation_cash'],rules,base.emit)
    session.positions={key:Decimal(value) for key,value in params.get('allocation_positions',{}).items()}
    context=StrategyContext(base,session);state=Reconciler(timedelta(seconds=5));state.reconcile(events[0].event_time,after)
    try:
        if callable(program.get('on_start')):program['on_start'](context)
        for event in events:
            if not state.apply(event):raise ValueError('paper source requires reconciliation')
            session.quote(event,True)
            intents=program['on_event'](context,event.model_copy(deep=True)) or []
            if not isinstance(intents,list):raise ValueError('on_event must return a list of LO intents')
            for intent in intents:session.place(event,intent,allocation,base.run_id)
            base.emit('paper_cursor',{'allocation_id':allocation,'snapshot_id':params['event_snapshot'],'sequence':event.sequence,'event_time':event.event_time.isoformat(),'instrument_id':event.instrument_id,'bid':event.bid,'ask':event.ask})
            time.sleep(.1)
    finally:
        session.close()
        if callable(program.get('on_stop')):program['on_stop'](context)
    base.emit('paper_session',{'mode':'synthetic-fixture-replay','allocation_id':allocation,'cash':str(session.cash),'positions':context.portfolio['positions'],'realtime':False})

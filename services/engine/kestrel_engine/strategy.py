"""Live-style callback contract; cannot run Backtest programs."""
import hashlib
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from .paper import PaperSession
from .sources import SourceBlocked
from .stream import Reconciler
from .tapes import TapeRepository
from .models import StrategySignal

class StrategyContext:
    def __init__(self,base,session,strategy_id,source='replay',mode='paper'):
        self.params=base.params;self._base=base;self._session=session;self.strategy_id=strategy_id;self.source=source;self.mode=mode;self._current_event=None;self._emitted_signal_ids=set()
    def log(self,message):self._base.log(message)
    def _set_event(self,event):self._current_event=event
    def signal(self,*,action:str,reason:str,logical_key:str,instrument_id:str|None=None,price_context:dict[str,str]|None=None,correlation_id:str|None=None,custom_action:str|None=None,expires_in_seconds:int=300):
        if self._current_event is None:raise ValueError('context.signal requires an active market event')
        if isinstance(expires_in_seconds,bool) or not isinstance(expires_in_seconds,int) or not 1<=expires_in_seconds<=300:
            raise ValueError('signal expiry must be between 1 and 300 seconds')
        event=self._current_event
        selected_instrument=instrument_id or event.instrument_id
        identity='\0'.join([self._base.run_id,event.id,selected_instrument,action,logical_key])
        signal_id=hashlib.sha256(identity.encode()).hexdigest()
        context=price_context if price_context is not None else {key:getattr(event,key) for key in ('bid','ask','price') if getattr(event,key) is not None}
        signal=StrategySignal(
            id=signal_id,run_id=self._base.run_id,strategy_id=self.strategy_id,
            instrument_id=selected_instrument,action=action,custom_action=custom_action,
            event_time=event.event_time,price_context=context,reason=reason,source=self.source,
            logical_key=logical_key,correlation_id=correlation_id,
            expires_at=event.event_time+timedelta(seconds=expires_in_seconds),
        )
        if signal.id in self._emitted_signal_ids:return signal
        self._base.emit('signal',signal.model_dump(mode='json'))
        self._emitted_signal_ids.add(signal.id)
        return signal
    @property
    def portfolio(self):
        if self._session is None:raise ValueError('portfolio is unavailable in signal_only mode')
        return {'cash':str(self._session.cash),'positions':{k:str(v) for k,v in self._session.positions.items()}}

def execute_program(program,base):
    params=base.params
    if params.get('paper_source')!='fixture-replay':raise SourceBlocked('SSI live paper feed, rights and rule validation remain unavailable')
    mode=params.get('strategy_mode','paper')
    if mode not in ['paper','signal_only']:raise ValueError('strategy_mode must be paper or signal_only')
    allocation=params.get('allocation_id')
    if mode=='paper' and not allocation:raise ValueError('choose a strategy allocation')
    repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures');events,rules=repo.load(params['event_snapshot'])
    after=int(params.get('after_sequence',0));events=[v for v in events if v.sequence>after]
    if not events:raise ValueError('fixture tape exhausted; existing positions remain held until eligible future data is available')
    session=None
    pending_mutations=[]
    if mode=='paper':
        session=PaperSession(params['allocation_cash'],rules,lambda kind,payload:pending_mutations.append({'type':kind,'payload':payload}))
        session.positions={key:Decimal(value) for key,value in params.get('allocation_positions',{}).items()}
    context=StrategyContext(base,session,str(params.get('strategy_id') or base.run_id),'replay',mode);state=Reconciler(timedelta(seconds=5));state.reconcile(events[0].event_time,after)
    completed=False
    try:
        if callable(program.get('on_start')):program['on_start'](context)
        for event in events:
            if not state.apply(event):raise ValueError('paper source requires reconciliation')
            context._set_event(event)
            pending_mutations.clear()
            if session is not None:session.quote(event,True)
            intents=program['on_event'](context,event.model_copy(deep=True)) or []
            if not isinstance(intents,list):raise ValueError('on_event must return a list of LO intents')
            if mode=='signal_only' and intents:raise ValueError('signal_only strategies cannot emit paper order intents')
            if session is not None:
                for intent in intents:session.place(event,intent,allocation,base.run_id)
                base.emit('paper_step',{'allocation_id':allocation,'snapshot_id':params['event_snapshot'],'after_sequence':event.sequence-1,'sequence':event.sequence,'event_time':event.event_time.isoformat(),'instrument_id':event.instrument_id,'bid':event.bid,'ask':event.ask,'mutations':pending_mutations.copy()})
            time.sleep(.1)
        completed=True
    finally:
        if session is not None and completed:
            pending_mutations.clear();session.close()
            for mutation in pending_mutations:base.emit(mutation['type'],mutation['payload'])
        if callable(program.get('on_stop')):program['on_stop'](context)
    if session is not None:base.emit('paper_session',{'mode':'synthetic-fixture-replay','allocation_id':allocation,'cash':str(session.cash),'positions':context.portfolio['positions'],'realtime':False})

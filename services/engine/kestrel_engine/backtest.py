"""Historical program contract, deliberately separate from live Strategy callbacks."""
from dataclasses import dataclass
from datetime import datetime,timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
import numpy as np
from .execution import FeeTaxSchedule,FillModelRegistry,MarketCalendar,Order,quote_fill
from .stream import Reconciler
from .tapes import TapeRepository

@dataclass(frozen=True)
class HistoricalView:
    history:tuple
    cash:str
    positions:MappingProxyType

class Replay:
    def __init__(self,events,rules,capital,calendar:MarketCalendar|None=None,cost_schedule:FeeTaxSchedule|None=None,fill_models=()):
        self.events=events;self.rules=rules.model_copy(deep=True);self.calendar=(calendar or MarketCalendar.from_rule_pack(self.rules)).model_copy(deep=True);self.cost_schedule=(cost_schedule or FeeTaxSchedule.from_rule_pack(self.rules)).model_copy(deep=True);self.fill_models=FillModelRegistry(fill_models);self.initial=Decimal(capital)
        if (self.calendar.venue,self.calendar.board)!=(self.rules.venue,self.rules.board):raise ValueError('calendar venue/board does not match selected rule pack')
        if (self.cost_schedule.venue,self.cost_schedule.board,self.cost_schedule.instrument_class)!=(self.rules.venue,self.rules.board,self.rules.instrument_class):raise ValueError('fee/tax schedule scope does not match selected rule pack')
        frozen_calendar=json.dumps(self.calendar.model_dump(mode='json'),sort_keys=True,separators=(',',':'))
        self.calendar_snapshot_id=hashlib.sha256(frozen_calendar.encode()).hexdigest()
        frozen_costs=json.dumps(self.cost_schedule.model_dump(mode='json'),sort_keys=True,separators=(',',':'))
        self.cost_schedule_snapshot_id=hashlib.sha256(frozen_costs.encode()).hexdigest()
        if not self.initial.is_finite() or self.initial<=0:raise ValueError('positive decimal capital required')
        self.cash=self.initial;self.orders=[];self.reserved={};self.positions={};self.settled={};self.pending_shares=[];self.pending_cash=[];self.sell_reserved={};self.fills=[];self.curve=[];self.marks={}
    def _simulation_coverage(self):
        if 'LO' not in self.rules.order_types:raise ValueError('simulation blocked: selected rules do not cover LO orders')
        quote_count=0;model_ids=set()
        for event in self.events:
            day=event.event_time.date()
            self.rules.check(day);self.calendar.check(day);self.cost_schedule.check(day)
            if event.is_synthetic!=self.rules.synthetic:raise ValueError('simulation blocked: data and rule provenance do not match')
            if event.kind!='quote':continue
            quote_count+=1
            if any(value is None for value in (event.bid,event.ask,event.bid_size,event.ask_size)):
                raise ValueError('simulation blocked: detailed quote liquidity fields are incomplete')
            parts=event.instrument_id.split(':')
            if len(parts)<4 or parts[:3]!=[self.rules.venue,self.rules.board,self.rules.instrument_class]:
                raise ValueError('simulation blocked: quote data does not match rule venue, board, and asset class')
            model=self.fill_models.resolve(self.rules.venue,self.rules.board,self.rules.instrument_class,'LO',self.rules.session,day)
            model_ids.add(model.id)
        if quote_count==0:raise ValueError('simulation blocked: detailed quote events are unavailable')
        return sorted(model_ids)
    def settle(self,day):
        for entry in self.pending_shares[:]:
            when,symbol,quantity=entry
            if when<=day:self.settled[symbol]=self.settled.get(symbol,Decimal(0))+quantity;self.pending_shares.remove(entry)
        for entry in self.pending_cash[:]:
            when,value=entry
            if when<=day:self.cash+=value;self.pending_cash.remove(entry)
    def place(self,event,intent):
        from .execution import validate_order
        order=Order(id=f'order-{len(self.orders)+1}-{event.sequence}',instrument_id=event.instrument_id,side=intent['side'],order_type='LO',limit_price=intent['limit_price'],quantity=intent['quantity'],created_at=event.received_at)
        validate_order(order,self.rules,event.event_time.date())
        self.cost_schedule.check(event.event_time.date())
        q=Decimal(order.quantity)
        if order.side=='buy':
            budget=Decimal(order.limit_price)*q*(1+Decimal(self.cost_schedule.fee_rate))
            if budget>self.cash:raise ValueError('insufficient backtest cash')
            self.cash-=budget;self.reserved[order.id]=budget
        else:
            available=self.settled.get(order.instrument_id,Decimal(0))-self.sell_reserved.get(order.instrument_id,Decimal(0))
            if q>available:raise ValueError('settled shares unavailable; shorting is excluded')
            self.sell_reserved[order.instrument_id]=self.sell_reserved.get(order.instrument_id,Decimal(0))+q
        self.orders.append({'order':order,'remaining':q})
    def nav(self):
        if any(quantity and symbol not in self.marks for symbol,quantity in self.positions.items()):raise ValueError('valuation price unavailable')
        return self.cash+sum(self.reserved.values())+sum(v for _,v in self.pending_cash)+sum(quantity*self.marks[symbol] for symbol,quantity in self.positions.items() if quantity)
    def run(self,decide):
        if not self.events:raise ValueError('no detailed events in selected period')
        fill_model_ids=self._simulation_coverage()
        state=Reconciler(timedelta(seconds=5));state.reconcile(self.events[0].event_time,self.events[0].sequence-1)
        visible=[]
        for event in self.events:
            self.calendar.check(event.event_time.date())
            self.settle(event.event_time.date())
            fresh=state.apply(event)
            if not fresh:raise ValueError('historical event gap/stale/order mismatch; replay blocked')
            if event.bid and event.ask:self.marks[event.instrument_id]=(Decimal(event.bid)+Decimal(event.ask))/2
            bid_left=Decimal(event.bid_size or '0');ask_left=Decimal(event.ask_size or '0')
            for pending in self.orders:
                order=pending['order']
                if pending['remaining']<=0:continue
                available=event.model_copy(update={'bid_size':str(bid_left),'ask_size':str(ask_left)})
                fill=quote_fill(order,available,self.rules,fresh,str(pending['remaining']),self.calendar,self.cost_schedule)
                if fill is None:continue
                q=Decimal(fill.quantity);price=Decimal(fill.price);fee=Decimal(fill.fee);tax=Decimal(fill.tax)
                if order.side=='buy':ask_left-=q
                else:bid_left-=q
                pending['remaining']-=q
                symbol=fill.instrument_id
                if fill.side=='buy':
                    released=Decimal(order.limit_price)*q*(1+Decimal(self.cost_schedule.fee_rate));self.reserved[order.id]-=released;self.cash+=released-price*q-fee
                    self.positions[symbol]=self.positions.get(symbol,Decimal(0))+q;self.pending_shares.append((fill.settlement_date,symbol,q))
                else:
                    self.positions[symbol]-=q;self.settled[symbol]-=q;self.sell_reserved[symbol]-=q;self.pending_cash.append((fill.settlement_date,price*q-fee-tax))
                self.fills.append(fill.model_dump(mode='json'))
                self.settle(event.event_time.date())
            visible.append(event.model_copy(deep=True))
            view=HistoricalView(tuple(visible),str(self.cash),MappingProxyType({k:str(v) for k,v in self.positions.items()}))
            intents=decide(view,event.model_copy(deep=True)) or []
            if not isinstance(intents,list):raise ValueError('backtest decision must return a list of LO intents')
            for intent in intents:self.place(event,intent)
            self.curve.append((event.event_time.isoformat(),str(self.nav())))
        self.cash+=sum(self.reserved.values());self.reserved.clear()
        values=np.array([float(v) for _,v in self.curve]);peak=np.maximum.accumulate(values);drawdown=(values/peak-1)
        return {'mode':'synthetic-detailed-replay','simulated':True,'capital':str(self.initial),'final_nav':str(self.nav()),'net_profit':str(self.nav()-self.initial),'max_drawdown':float(drawdown.min()),'simulated_fill_count':len(self.fills),'sharpe':None,'sharpe_reason':'risk-free/annualization convention not configured','positions':{k:str(v) for k,v in self.positions.items()},'unsettled_cash':str(sum(v for _,v in self.pending_cash)),'curve':self.curve,'fills':self.fills,'rule_pack':self.rules.id,'calendar_id':self.calendar.id,'calendar_snapshot_id':self.calendar_snapshot_id,'fee_tax_schedule_id':self.cost_schedule.id,'fee_tax_schedule_snapshot_id':self.cost_schedule_snapshot_id,'fill_model_ids':fill_model_ids,'fill_model':'displayed-quote-crossing; historical queue not reconstructed'}

class BacktestContext:
    def __init__(self,base):self._base=base;self.params=base.params;self._report=None
    def log(self,message):self._base.log(message)
    def table(self,*args):return self._base.table(*args)
    def chart(self,*args):return self._base.chart(*args)
    def replay(self,decide):
        params=self.params
        def instant(key):
            value=datetime.fromisoformat(str(params[key]))
            if value.tzinfo is None:raise ValueError('Train/Test dates require timezone')
            return value
        train_start,train_end,test_start,test_end=[instant(v) for v in ['train_start','train_end','test_start','test_end']]
        if not train_start<train_end<test_start<test_end:raise ValueError('Train/Test ranges must be ordered and non-overlapping')
        stage=params.get('stage','train')
        if stage not in ['train','test']:raise ValueError('choose train or test')
        if stage=='test' and not params.get('train_run_id'):raise ValueError('Test requires a frozen completed Train run')
        a,b=(train_start,train_end) if stage=='train' else (test_start,test_end)
        repo=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures')
        events,rules=repo.load(params['event_snapshot'])
        events=[v for v in events if a<=v.event_time<=b]
        report=Replay(events,rules,params['capital'],fill_models=repo.fill_models(params['event_snapshot'])).run(decide)
        report.update({'stage':stage,'event_snapshot':params['event_snapshot'],'train_run_id':params.get('train_run_id')})
        self._report=report
        return report

def execute_program(program,base):
    context=BacktestContext(base)
    program['run'](context)
    if context._report is None:raise ValueError('Backtest program must call context.replay(decide)')
    report=context._report
    base.emit('backtest_report',{key:value for key,value in report.items() if key not in ['fills','curve']})
    base.chart('NAV',[t for t,_ in report['curve']],[float(v) for _,v in report['curve']])
    base.table('fills',['time','side','quantity','price','fee','tax'],[[v['event_time'],v['side'],v['quantity'],v['price'],v['fee'],v['tax']] for v in report['fills']])

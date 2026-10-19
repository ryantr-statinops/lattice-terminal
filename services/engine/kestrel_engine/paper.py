"""Paper callback engine; independent of the Backtest program API."""
from decimal import Decimal
from .execution import Order,quote_fill,validate_order

class PaperSession:
    def __init__(self,capital,rules,emit):
        self.cash=Decimal(capital);self.rules=rules;self.emit=emit;self.orders=[];self.positions={};self.counter=0
        if not self.cash.is_finite() or self.cash<=0:raise ValueError('positive paper capital required')
        if not rules.synthetic:raise ValueError('production rule/settlement/feed validation is pending')
    def place(self,event,intent,allocation,run_id):
        self.counter+=1
        order=Order(id=f'{run_id}-{self.counter}',instrument_id=event.instrument_id,side=intent['side'],order_type='LO',limit_price=intent['limit_price'],quantity=intent['quantity'],created_at=event.received_at)
        validate_order(order,self.rules,event.event_time.date())
        quantity=Decimal(order.quantity);budget=quantity*Decimal(order.limit_price)*(1+Decimal(self.rules.fee_rate))
        if order.side=='buy':
            if budget>self.cash:raise ValueError('paper allocation cash insufficient')
            self.cash-=budget
        elif quantity>self.positions.get(order.instrument_id,Decimal(0))-sum(v['remaining'] for v in self.orders if v['order'].side=='sell' and v['order'].instrument_id==order.instrument_id):raise ValueError('settled paper position insufficient')
        self.orders.append({'order':order,'remaining':quantity})
        self.emit('paper_order',order.model_dump(mode='json')|{'allocation_id':allocation,'reserve_rate':self.rules.fee_rate})
    def quote(self,event,fresh):
        bid=Decimal(event.bid_size or '0');ask=Decimal(event.ask_size or '0')
        for pending in self.orders:
            if pending['remaining']<=0:continue
            order=pending['order'];available=event.model_copy(update={'bid_size':str(bid),'ask_size':str(ask)})
            fill=quote_fill(order,available,self.rules,fresh,str(pending['remaining']))
            if fill is None:continue
            q=Decimal(fill.quantity);pending['remaining']-=q
            if fill.side=='buy':
                ask-=q;release=Decimal(order.limit_price)*q*(1+Decimal(self.rules.fee_rate));self.cash+=release-Decimal(fill.price)*q-Decimal(fill.fee)-Decimal(fill.tax);self.positions[order.instrument_id]=self.positions.get(order.instrument_id,Decimal(0))+q
            else:bid-=q;self.cash+=Decimal(fill.price)*q-Decimal(fill.fee)-Decimal(fill.tax);self.positions[order.instrument_id]-=q
            self.emit('paper_fill',fill.model_dump(mode='json'))
    def close(self):
        for pending in self.orders:
            if pending['remaining']>0:self.emit('paper_cancel',{'order_id':pending['order'].id});pending['remaining']=Decimal(0)

"""Detailed quote fill approximation. Never accepts OHLC as executable liquidity."""
from datetime import date
from decimal import Decimal,ROUND_FLOOR
from typing import Iterable,Literal
from pydantic import AwareDatetime,Field,field_validator
from .models import Record,decimal_text
from .stream import MarketEvent

class RulePack(Record):
    id:str
    venue:str
    board:str='REGULAR'
    instrument_class:Literal['equity']='equity'
    effective_from:date
    effective_to:date
    synthetic:bool=False
    verified:bool=False
    evidence:list[str]=[]
    order_types:list[str]
    session:str
    tick:str
    lot:str
    fee_rate:str
    sell_tax_rate:str
    settlement_days:int=Field(ge=0)
    settlement_calendar:list[date]
    @field_validator('tick','lot','fee_rate','sell_tax_rate')
    @classmethod
    def number(cls,v):return decimal_text(v)
    def check(self,day:date):
        if not self.effective_from<=day<=self.effective_to:raise ValueError('no effective-dated rule pack')
        if not self.synthetic and (not self.verified or not self.evidence):raise ValueError('venue rules require verified evidence')
        if Decimal(self.tick)<=0 or Decimal(self.lot)<=0:raise ValueError('invalid tick/lot')
        if not Decimal(0)<=Decimal(self.fee_rate)<=1 or not Decimal(0)<=Decimal(self.sell_tax_rate)<=1:raise ValueError('invalid cost assumption')
        if day not in self.settlement_calendar:raise ValueError('session calendar unavailable')
    def settlement(self,day:date):
        self.check(day)
        calendar=sorted(set(self.settlement_calendar));index=calendar.index(day)+self.settlement_days
        if index>=len(calendar):raise ValueError('settlement calendar coverage missing')
        return calendar[index]

class RulePackRegistry:
    """Select one immutable venue rule pack by instrument identity and effective date."""

    def __init__(self, packs: Iterable[RulePack] = ()):
        self._packs: dict[str, RulePack] = {}
        for pack in packs:
            self.register(pack)

    def register(self, pack: RulePack) -> None:
        if pack.id in self._packs:
            raise ValueError(f'duplicate rule pack id: {pack.id}')
        for existing in self._packs.values():
            same_scope = (
                existing.venue == pack.venue
                and existing.board == pack.board
                and existing.instrument_class == pack.instrument_class
            )
            overlaps = pack.effective_from <= existing.effective_to and existing.effective_from <= pack.effective_to
            if same_scope and overlaps:
                raise ValueError(f'overlapping rule pack effective dates: {existing.id} and {pack.id}')
        self._packs[pack.id] = pack

    def get(self, rule_pack_id: str) -> RulePack:
        try:
            return self._packs[rule_pack_id]
        except KeyError as error:
            raise ValueError(f'rule pack not registered: {rule_pack_id}') from error

    def resolve(self, venue: str, board: str, instrument_class: str, day: date) -> RulePack:
        matches = [
            pack for pack in self._packs.values()
            if pack.venue == venue
            and pack.board == board
            and pack.instrument_class == instrument_class
            and pack.effective_from <= day <= pack.effective_to
        ]
        if not matches:
            raise ValueError('no effective-dated rule pack for venue, board, class, and date')
        if len(matches) > 1:
            raise ValueError('ambiguous effective-dated rule pack')
        return matches[0]

class Order(Record):
    id:str
    instrument_id:str
    side:Literal['buy','sell']
    order_type:str
    limit_price:str
    quantity:str
    created_at:AwareDatetime
    @field_validator('limit_price','quantity')
    @classmethod
    def number(cls,v):
        decimal_text(v)
        if Decimal(v)<=0:raise ValueError('positive order values required')
        return v

class Fill(Record):
    order_id:str
    instrument_id:str
    side:str
    quantity:str
    price:str
    fee:str
    tax:str
    event_id:str
    event_time:AwareDatetime
    settlement_date:date
    rule_pack_id:str
    simulated:Literal[True]=True
    model:str='displayed-quote-crossing; queue priority not reconstructed'

def validate_order(order:Order,rules:RulePack,day:date):
    rules.check(day)
    parts=order.instrument_id.split(':')
    if len(parts)!=4 or parts[:3]!=[rules.venue,rules.board,rules.instrument_class]:raise ValueError('instrument venue/board/class does not match rule pack')
    if order.order_type not in rules.order_types:raise ValueError('order type unsupported for venue/rules')
    if order.order_type!='LO':raise ValueError('auction/market-order fill capability not yet verified or implemented')
    if Decimal(order.limit_price)%Decimal(rules.tick)!=0 or Decimal(order.quantity)%Decimal(rules.lot)!=0:raise ValueError('tick/lot violation')

def quote_fill(order:Order,event:MarketEvent,rules:RulePack,fresh:bool,remaining:str|None=None)->Fill|None:
    validate_order(order,rules,event.event_time.date())
    if not fresh or event.instrument_id!=order.instrument_id or event.kind!='quote' or event.session!=rules.session or event.trading_status!='trading':return None
    if event.event_time<=order.created_at:return None
    if rules.synthetic!=event.is_synthetic:raise ValueError('synthetic/production boundary mismatch')
    price=event.ask if order.side=='buy' else event.bid
    size=event.ask_size if order.side=='buy' else event.bid_size
    if price is None or size is None:return None
    decimal_text(price);decimal_text(size)
    p=Decimal(price);available=Decimal(size)
    if p<=0 or available<=0:return None
    limit=Decimal(order.limit_price)
    if (order.side=='buy' and p>limit) or (order.side=='sell' and p<limit):return None
    amount=min(Decimal(remaining or order.quantity),available)
    amount=(amount/Decimal(rules.lot)).to_integral_value(rounding=ROUND_FLOOR)*Decimal(rules.lot)
    if amount<=0:return None
    gross=p*amount
    return Fill(order_id=order.id,instrument_id=order.instrument_id,side=order.side,quantity=str(amount),price=str(p),fee=str(gross*Decimal(rules.fee_rate)),tax=str(gross*Decimal(rules.sell_tax_rate) if order.side=='sell' else Decimal(0)),event_id=event.id,event_time=event.event_time,settlement_date=rules.settlement(event.event_time.date()),rule_pack_id=rules.id)

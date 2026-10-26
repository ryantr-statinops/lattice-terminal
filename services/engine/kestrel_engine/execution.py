"""Detailed quote fill approximation. Never accepts OHLC as executable liquidity."""
from datetime import date
from decimal import Decimal,ROUND_FLOOR
from typing import Iterable,Literal
from pydantic import AwareDatetime,ConfigDict,Field,field_validator
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

class MarketCalendar(Record):
    """Immutable trading-date snapshot selected for one venue and board."""

    model_config = ConfigDict(extra='forbid', frozen=True)
    id: str
    venue: str
    board: str
    effective_from: date
    effective_to: date
    trading_dates: tuple[date, ...] = Field(min_length=1)
    synthetic: bool = False
    verified: bool = False
    evidence: tuple[str, ...] = ()

    @field_validator('trading_dates')
    @classmethod
    def ordered_unique_dates(cls, value):
        if tuple(sorted(set(value))) != value:
            raise ValueError('calendar trading dates must be unique and ordered')
        return value

    def check(self, day: date) -> None:
        if not self.effective_from <= day <= self.effective_to:
            raise ValueError('calendar date outside effective coverage')
        if day not in self.trading_dates:
            raise ValueError('calendar marks date as non-trading')
        if not self.synthetic and (not self.verified or not self.evidence):
            raise ValueError('production calendar requires verified evidence')

    def settlement(self, day: date, settlement_days: int) -> date:
        self.check(day)
        index = self.trading_dates.index(day) + settlement_days
        if index >= len(self.trading_dates):
            raise ValueError('calendar settlement coverage missing')
        return self.trading_dates[index]

    @classmethod
    def from_rule_pack(cls, rules: RulePack) -> 'MarketCalendar':
        return cls(
            id=f'{rules.id}:calendar',
            venue=rules.venue,
            board=rules.board,
            effective_from=rules.effective_from,
            effective_to=rules.effective_to,
            trading_dates=tuple(sorted(set(rules.settlement_calendar))),
            synthetic=rules.synthetic,
            verified=rules.verified,
            evidence=tuple(rules.evidence),
        )


class CalendarRegistry:
    """Resolve effective-dated calendars without overlapping venue/board coverage."""

    def __init__(self, calendars: Iterable[MarketCalendar] = ()):
        self._calendars: dict[str, MarketCalendar] = {}
        for calendar in calendars:
            self.register(calendar)

    def register(self, calendar: MarketCalendar) -> None:
        if calendar.id in self._calendars:
            raise ValueError(f'duplicate calendar id: {calendar.id}')
        for existing in self._calendars.values():
            same_scope = existing.venue == calendar.venue and existing.board == calendar.board
            overlaps = calendar.effective_from <= existing.effective_to and existing.effective_from <= calendar.effective_to
            if same_scope and overlaps:
                raise ValueError(f'overlapping calendar coverage: {existing.id} and {calendar.id}')
        self._calendars[calendar.id] = calendar

    def resolve(self, venue: str, board: str, day: date) -> MarketCalendar:
        matches = [
            calendar for calendar in self._calendars.values()
            if calendar.venue == venue and calendar.board == board
            and calendar.effective_from <= day <= calendar.effective_to
        ]
        if not matches:
            raise ValueError('no calendar for venue, board, and date')
        if len(matches) > 1:
            raise ValueError('ambiguous calendar coverage')
        matches[0].check(day)
        return matches[0]

class FeeTaxSchedule(Record):
    """Immutable version of transaction costs for a venue and instrument class."""

    model_config = ConfigDict(extra='forbid', frozen=True)
    id: str
    venue: str
    board: str
    instrument_class: str
    effective_from: date
    effective_to: date
    fee_rate: str
    sell_tax_rate: str
    synthetic: bool = False
    verified: bool = False
    evidence: tuple[str, ...] = ()

    @field_validator('fee_rate','sell_tax_rate')
    @classmethod
    def valid_rate(cls, value):
        decimal_text(value)
        if not Decimal(0) <= Decimal(value) <= 1:
            raise ValueError('fee and tax rates must be between zero and one')
        return value

    def check(self, day: date) -> None:
        if not self.effective_from <= day <= self.effective_to:
            raise ValueError('no effective-dated fee/tax schedule')
        if not self.synthetic and (not self.verified or not self.evidence):
            raise ValueError('production fee/tax schedule requires verified evidence')

    @classmethod
    def from_rule_pack(cls, rules: RulePack) -> 'FeeTaxSchedule':
        return cls(
            id=f'{rules.id}:costs', venue=rules.venue, board=rules.board,
            instrument_class=rules.instrument_class, effective_from=rules.effective_from,
            effective_to=rules.effective_to, fee_rate=rules.fee_rate,
            sell_tax_rate=rules.sell_tax_rate, synthetic=rules.synthetic,
            verified=rules.verified, evidence=tuple(rules.evidence),
        )


class FeeTaxScheduleRegistry:
    def __init__(self, schedules: Iterable[FeeTaxSchedule] = ()):
        self._schedules: dict[str, FeeTaxSchedule] = {}
        for schedule in schedules:
            self.register(schedule)

    def register(self, schedule: FeeTaxSchedule) -> None:
        if schedule.id in self._schedules:
            raise ValueError(f'duplicate fee/tax schedule id: {schedule.id}')
        for existing in self._schedules.values():
            same_scope = (
                existing.venue == schedule.venue
                and existing.board == schedule.board
                and existing.instrument_class == schedule.instrument_class
            )
            overlaps = schedule.effective_from <= existing.effective_to and existing.effective_from <= schedule.effective_to
            if same_scope and overlaps:
                raise ValueError(f'overlapping fee/tax schedule dates: {existing.id} and {schedule.id}')
        self._schedules[schedule.id] = schedule

    def resolve(self, venue: str, board: str, instrument_class: str, day: date) -> FeeTaxSchedule:
        matches = [
            schedule for schedule in self._schedules.values()
            if schedule.venue == venue and schedule.board == board
            and schedule.instrument_class == instrument_class
            and schedule.effective_from <= day <= schedule.effective_to
        ]
        if not matches:
            raise ValueError('no fee/tax schedule for venue, class, and date')
        if len(matches) > 1:
            raise ValueError('ambiguous fee/tax schedule')
        matches[0].check(day)
        return matches[0]

class FillModel(Record):
    id: str
    venue: str
    board: str
    instrument_class: str
    order_type: str
    session: str
    effective_from: date
    effective_to: date
    implementation: Literal['displayed_quote_crossing']
    synthetic: bool = False
    implemented: bool = True
    verified: bool = False
    evidence: list[str] = []

    def check(self, day: date) -> None:
        if not self.effective_from <= day <= self.effective_to:
            raise ValueError('no effective-dated fill model')
        if not self.implemented:
            raise ValueError('fill model implementation unavailable')
        if not self.synthetic and (not self.verified or not self.evidence):
            raise ValueError('production fill model requires verified evidence')


class FillModelRegistry:
    """Select a fill implementation only for its declared market coverage."""

    def __init__(self, models: Iterable[FillModel] = ()):
        self._models: dict[str, FillModel] = {}
        for model in models:
            self.register(model)

    def register(self, model: FillModel) -> None:
        if model.id in self._models:
            raise ValueError(f'duplicate fill model id: {model.id}')
        for existing in self._models.values():
            same_scope = (
                existing.venue == model.venue
                and existing.board == model.board
                and existing.instrument_class == model.instrument_class
                and existing.order_type == model.order_type
                and existing.session == model.session
            )
            overlaps = model.effective_from <= existing.effective_to and existing.effective_from <= model.effective_to
            if same_scope and overlaps:
                raise ValueError(f'overlapping fill model coverage: {existing.id} and {model.id}')
        self._models[model.id] = model

    def resolve(
        self,
        venue: str,
        board: str,
        instrument_class: str,
        order_type: str,
        session: str,
        day: date,
    ) -> FillModel:
        matches = [
            model for model in self._models.values()
            if model.venue == venue
            and model.board == board
            and model.instrument_class == instrument_class
            and model.order_type == order_type
            and model.session == session
            and model.effective_from <= day <= model.effective_to
        ]
        if not matches:
            raise ValueError('no fill model for venue, class, order type, session, and date')
        if len(matches) > 1:
            raise ValueError('ambiguous fill model coverage')
        matches[0].check(day)
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
    fee_tax_schedule_id:str|None=None
    simulated:Literal[True]=True
    model:str='displayed-quote-crossing; queue priority not reconstructed'

def validate_order(order:Order,rules:RulePack,day:date,calendar:MarketCalendar|None=None):
    rules.check(day)
    if calendar is not None:calendar.check(day)
    parts=order.instrument_id.split(':')
    if len(parts)!=4 or parts[:3]!=[rules.venue,rules.board,rules.instrument_class]:raise ValueError('instrument venue/board/class does not match rule pack')
    if order.order_type not in rules.order_types:raise ValueError('order type unsupported for venue/rules')
    if order.order_type!='LO':raise ValueError('auction/market-order fill capability not yet verified or implemented')
    if Decimal(order.limit_price)%Decimal(rules.tick)!=0 or Decimal(order.quantity)%Decimal(rules.lot)!=0:raise ValueError('tick/lot violation')

def quote_fill(order:Order,event:MarketEvent,rules:RulePack,fresh:bool,remaining:str|None=None,calendar:MarketCalendar|None=None,cost_schedule:FeeTaxSchedule|None=None)->Fill|None:
    validate_order(order,rules,event.event_time.date(),calendar)
    if cost_schedule is not None:
        cost_schedule.check(event.event_time.date())
        if (cost_schedule.venue,cost_schedule.board,cost_schedule.instrument_class)!=(rules.venue,rules.board,rules.instrument_class):
            raise ValueError('fee/tax schedule scope does not match selected rule pack')
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
    settlement_date=calendar.settlement(event.event_time.date(),rules.settlement_days) if calendar is not None else rules.settlement(event.event_time.date())
    fee_rate=cost_schedule.fee_rate if cost_schedule is not None else rules.fee_rate
    sell_tax_rate=cost_schedule.sell_tax_rate if cost_schedule is not None else rules.sell_tax_rate
    return Fill(order_id=order.id,instrument_id=order.instrument_id,side=order.side,quantity=str(amount),price=str(p),fee=str(gross*Decimal(fee_rate)),tax=str(gross*Decimal(sell_tax_rate) if order.side=='sell' else Decimal(0)),event_id=event.id,event_time=event.event_time,settlement_date=settlement_date,rule_pack_id=rules.id,fee_tax_schedule_id=cost_schedule.id if cost_schedule is not None else None)

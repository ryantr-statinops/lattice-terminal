"""Detailed replay data and paper order endpoints."""
from decimal import Decimal
from fastapi import APIRouter
from ..context import EngineServices
from ..schemas import PaperEvaluate, PaperPrepare
from ...execution.tapes import TapeRepository
from ...execution.rules import Order, quote_fill, validate_order

def build_paper_router(services: EngineServices) -> APIRouter:
    router = APIRouter()
    fixture_root = services.fixture_root
    @router.get('/internal/v1/backtest/data')
    def detailed_data():return [TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures').manifest()]

    @router.post('/internal/v1/paper/prepare')
    def prepare_order(value:PaperPrepare):
        events,rules=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures').load(value.snapshot)
        if value.sequence<1 or value.sequence>len(events):raise ValueError('advance fixture clock before placing an order')
        event=events[value.sequence-1]
        order=Order(id=value.id,instrument_id=event.instrument_id,side=value.side,order_type='LO',limit_price=value.limit_price,quantity=value.quantity,created_at=event.received_at)
        validate_order(order,rules,event.event_time.date())
        return order.model_dump(mode='json')|{'reserve_rate':rules.fee_rate}

    @router.post('/internal/v1/paper/evaluate')
    def evaluate_paper(value:PaperEvaluate):
        events,rules=TapeRepository(Path(__file__).resolve().parents[3]/'data/fixtures').load(value.snapshot)
        if value.after<0 or value.after>=len(events):raise ValueError('fixture tape exhausted or invalid cursor')
        event=events[value.after];fills=[];bid=Decimal(event.bid_size or '0');ask=Decimal(event.ask_size or '0')
        for raw in value.orders:
            if raw['status']!='open':continue
            order=Order(id=raw['id'],instrument_id=raw['instrument_id'],side=raw['side'],order_type='LO',limit_price=raw['limit_price'],quantity=raw['quantity'],created_at=raw['created_at'])
            available=event.model_copy(update={'bid_size':str(bid),'ask_size':str(ask)})
            fill=quote_fill(order,available,rules,True,raw['remaining'])
            if fill:
                fills.append(fill)
                if fill.side=='buy':ask-=Decimal(fill.quantity)
                else:bid-=Decimal(fill.quantity)
        return {'event':event,'fills':fills}

    return router

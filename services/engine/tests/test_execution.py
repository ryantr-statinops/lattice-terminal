from datetime import date,datetime,timedelta,timezone
import pytest
from kestrel_engine.execution import Order,RulePack,RulePackRegistry,quote_fill
from kestrel_engine.stream import MarketEvent

def fixture():
    at=datetime(2026,10,1,2,tzinfo=timezone.utc)
    rule=RulePack(id='SYNTHETIC-ONLY',venue='HOSE',effective_from=date(2026,1,1),effective_to=date(2026,12,31),synthetic=True,order_types=['LO'],session='synthetic-continuous',tick='1',lot='1',fee_rate='0',sell_tax_rate='0',settlement_days=0,settlement_calendar=[at.date()])
    order=Order(id='order',instrument_id='HOSE:REGULAR:equity:SYN',side='buy',order_type='LO',limit_price='100',quantity='10',created_at=at)
    event=MarketEvent(id='quote-1',instrument_id='HOSE:REGULAR:equity:SYN',feed='quote',sequence=1,event_time=at+timedelta(seconds=1),received_at=at+timedelta(seconds=1),source_id='SYNTHETIC-FIXTURE',is_synthetic=True,kind='quote',session='synthetic-continuous',trading_status='trading',ask='99',ask_size='4')
    return rule,order,event

def test_fill_uses_subsequent_fresh_detailed_quote_and_size():
    rule,order,event=fixture();fill=quote_fill(order,event,rule,True)
    assert fill.quantity=='4' and fill.price=='99' and fill.simulated
    assert quote_fill(order,event,rule,False) is None
    assert quote_fill(order,event.model_copy(update={'event_time':order.created_at}),rule,True) is None
    assert quote_fill(order,event.model_copy(update={'kind':'bar'}),rule,True) is None

def test_real_rules_require_evidence_and_historical_effective_dates():
    rule,order,event=fixture()
    with pytest.raises(ValueError,match='evidence'):quote_fill(order,event,rule.model_copy(update={'synthetic':False}),True)
    with pytest.raises(ValueError,match='effective'):quote_fill(order,event,rule.model_copy(update={'effective_to':date(2025,1,1)}),True)

def test_rule_pack_cannot_be_applied_to_another_venue_or_board():
    rule,order,event=fixture()
    for identity in ['HNX:REGULAR:equity:SYN','HOSE:ODD:equity:SYN','HOSE:REGULAR:derivative:SYN']:
        with pytest.raises(ValueError,match='venue/board/class'):quote_fill(order.model_copy(update={'instrument_id':identity}),event,rule,True)

def test_rule_pack_registry_resolves_effective_dates_and_rejects_gaps():
    rule,_,_=fixture()
    next_rule=rule.model_copy(update={
        'id':'SYNTHETIC-NEXT',
        'effective_from':date(2027,1,1),
        'effective_to':date(2027,12,31),
    })
    registry=RulePackRegistry([rule,next_rule])
    assert registry.resolve('HOSE','REGULAR','equity',date(2026,10,1)).id=='SYNTHETIC-ONLY'
    assert registry.resolve('HOSE','REGULAR','equity',date(2027,1,1)).id=='SYNTHETIC-NEXT'
    assert registry.get('SYNTHETIC-ONLY') is rule
    with pytest.raises(ValueError,match='no effective-dated rule pack'):
        registry.resolve('HOSE','REGULAR','equity',date(2028,1,1))

def test_rule_pack_registry_rejects_overlapping_rules_for_same_scope():
    rule,_,_=fixture()
    overlapping=rule.model_copy(update={'id':'OVERLAPPING'})
    with pytest.raises(ValueError,match='overlapping rule pack'):
        RulePackRegistry([rule,overlapping])

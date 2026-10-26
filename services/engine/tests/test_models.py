from datetime import datetime
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from kestrel_engine.models import Candle,Instrument,OrderBookDepth,Quote,Trade,decimal_text

def test_fixture_contract_and_strict_decimals():
    root=Path(__file__).resolve().parents[3]
    raw=json.loads((root/'data/fixtures/SYN01.json').read_text())['candles'][0]
    assert Candle.model_validate(raw).is_closed
    assert Candle.model_validate(raw).open_time.utcoffset().total_seconds()==0
    for value in [1.5,'NaN','Infinity','oops']:
        with pytest.raises(ValueError): decimal_text(value)
    with pytest.raises(ValidationError): Candle.model_validate(raw|{'open_time':'2026-01-01T00:00:00'})
    with pytest.raises(ValidationError): Candle.model_validate(raw|{'high':'1'})
from kestrel_engine.models import ProviderInstrumentAlias


def test_provider_instrument_alias_keeps_provider_identity_separate():
    alias = ProviderInstrumentAlias(
        stable_instrument_id='vn-equity:HOSE:HPG',
        provider_id='provider-a',
        provider_instrument_id='listing-123',
        native_symbol='HPG',
        venue='HOSE',
    )
    assert alias.stable_instrument_id == 'vn-equity:HOSE:HPG'
    assert alias.provider_instrument_id == 'listing-123'
    assert alias.provider_id == 'provider-a'


def test_provider_instrument_alias_rejects_blank_identity():
    with pytest.raises(ValueError, match='must not be blank'):
        ProviderInstrumentAlias(
            stable_instrument_id='vn-equity:HOSE:HPG',
            provider_id='provider-a',
            provider_instrument_id='listing-123',
            native_symbol=' ',
        )


@pytest.mark.parametrize('instrument_class', ['equity', 'covered_warrant', 'derivative', 'bond', 'fund', 'etf', 'macro_series'])
def test_instrument_accepts_additional_asset_classes(instrument_class):
    instrument = Instrument(
        id='provider:instrument-1',
        venue='HOSE',
        board='MAIN',
        native_symbol='TEST',
        instrument_class=instrument_class,
        name='Test instrument',
    )
    assert instrument.instrument_class == instrument_class


def test_instrument_preserves_asset_specific_metadata():
    instrument = Instrument(
        id='provider:future-123',
        venue='HNX',
        board='DERIVATIVES',
        native_symbol='VN30F2612',
        instrument_class='derivative',
        name='VN30 Futures Dec 2026',
        metadata={'underlying': 'VN30', 'expiry': '2026-12-17', 'multiplier': '100000'},
    )
    assert instrument.metadata['underlying'] == 'VN30'
    assert instrument.metadata['multiplier'] == '100000'


def test_candle_contract_accepts_additional_intervals():
    root=Path(__file__).resolve().parents[3]
    raw=json.loads((root/'data/fixtures/SYN01.json').read_text())['candles'][0]
    assert Candle.model_validate(raw | {'interval':'15m'}).interval == '15m'


def test_trade_record_preserves_event_and_availability_times():
    event = datetime.fromisoformat('2026-10-26T03:00:00+00:00')
    trade = Trade(
        instrument_id='vn-equity:HOSE:HPG', trade_id='trade-1',
        event_time=event, available_at=event.replace(minute=1),
        price='25.10', quantity='100', side='buy', source_id='fixture',
    )
    assert trade.available_at > trade.event_time
    with pytest.raises(ValueError, match='trade quantity must be positive'):
        Trade(
            instrument_id='vn-equity:HOSE:HPG', trade_id='trade-2',
            event_time=event, available_at=event, price='25.10',
            quantity='0', source_id='fixture',
        )


def test_quote_record_validates_bid_ask_and_sizes():
    event = datetime.fromisoformat('2026-10-26T03:00:00+00:00')
    quote = Quote(
        instrument_id='vn-equity:HOSE:HPG', event_time=event,
        available_at=event, bid_price='25.10', bid_size='100',
        ask_price='25.15', ask_size='200', source_id='fixture',
    )
    assert quote.bid_price == '25.10'
    with pytest.raises(ValueError, match='bid price cannot exceed ask price'):
        Quote(
            instrument_id='vn-equity:HOSE:HPG', event_time=event,
            available_at=event, bid_price='25.20', ask_price='25.15',
            source_id='fixture',
        )


def test_order_book_depth_requires_price_ordering_by_side():
    event = datetime.fromisoformat('2026-10-26T03:00:00+00:00')
    depth = OrderBookDepth(
        instrument_id='vn-equity:HOSE:HPG', event_time=event,
        available_at=event, bids=[{'price':'25.10','quantity':'100'}, {'price':'25.05','quantity':'200'}],
        asks=[{'price':'25.15','quantity':'100'}, {'price':'25.20','quantity':'100'}],
        source_id='fixture',
    )
    assert depth.bids[0].price == '25.10'
    with pytest.raises(ValueError, match='bid depth must be sorted'):
        OrderBookDepth(
            instrument_id='vn-equity:HOSE:HPG', event_time=event,
            available_at=event, bids=[{'price':'25.05','quantity':'1'}, {'price':'25.10','quantity':'1'}],
            source_id='fixture',
        )

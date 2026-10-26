from datetime import datetime
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from kestrel_engine.models import Candle,CorporateAction,DatasetEnvelope,FinancialStatement,Instrument,OrderBookDepth,ProviderInstrumentAlias,Quote,StrategySignal,Trade,ValueSeriesPoint,decimal_text

def test_fixture_contract_and_strict_decimals():
    root=Path(__file__).resolve().parents[3]
    raw=json.loads((root/'data/fixtures/SYN01.json').read_text())['candles'][0]
    assert Candle.model_validate(raw).is_closed
    assert Candle.model_validate(raw).open_time.utcoffset().total_seconds()==0
    for value in [1.5,'NaN','Infinity','oops']:
        with pytest.raises(ValueError): decimal_text(value)
    with pytest.raises(ValidationError): Candle.model_validate(raw|{'open_time':'2026-01-01T00:00:00'})
    with pytest.raises(ValidationError): Candle.model_validate(raw|{'high':'1'})
def test_provider_instrument_alias_keeps_provider_identity_separate():
    alias = ProviderInstrumentAlias(
        stable_instrument_id='vn-equity:HOSE:HPG',
        provider_id='provider-a',
        provider_instrument_id='listing-123',
        native_symbol='HPG',
        venue='HOSE',
        effective_from='2026-01-01T00:00:00Z',
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
            effective_from='2026-01-01T00:00:00Z',
        )


def test_provider_instrument_alias_rejects_reversed_effective_range():
    with pytest.raises(ValidationError, match='effective_to must be later'):
        ProviderInstrumentAlias(
            stable_instrument_id='vn-equity:HOSE:HPG',
            provider_id='provider-a',
            provider_instrument_id='listing-123',
            native_symbol='HPG',
            effective_from='2026-06-01T00:00:00Z',
            effective_to='2026-01-01T00:00:00Z',
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


def test_instrument_accepts_other_and_unspecified_venues():
    overseas = Instrument(
        id='provider:NYSE:ABC', venue='NYSE', board='MAIN',
        native_symbol='ABC', instrument_class='equity', name='Example Corp',
    )
    macro = Instrument(
        id='provider:macro:policy-rate', venue=None, board='SERIES',
        native_symbol='POLICY_RATE', instrument_class='macro_series',
        name='Policy rate',
    )
    assert overseas.venue == 'NYSE'
    assert macro.venue is None


def test_instrument_without_class_remains_unclassified():
    instrument = Instrument(
        id='provider:unknown:TEST', venue=None, board='UNKNOWN',
        native_symbol='TEST', name='Unclassified instrument',
    )
    assert instrument.instrument_class == 'unknown'


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
    assert Candle.model_validate(raw).currency == 'unknown'
    declared = Candle.model_validate(raw | {
        'currency':'VND', 'price_unit':'VND/share', 'volume_unit':'share',
    })
    assert declared.currency == 'VND'
    assert declared.price_unit == 'VND/share'


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


def test_dataset_envelope_keeps_provenance_revision_and_publication_time():
    observed = datetime.fromisoformat('2026-10-26T03:02:00+00:00')
    envelope = DatasetEnvelope(
        provider_id='provider-a', dataset='macro.policy-rate', source_id='provider-a',
        observed_at=observed, available_at=observed,
        published_at=datetime.fromisoformat('2026-10-26T03:00:00+00:00'),
        revision='3', schema_version='2', parser_version='1.4.0',
        quality='complete', payload={'rate':'4.5','unit':'percent'},
    )
    assert envelope.revision == '3'
    assert envelope.published_at < envelope.available_at
    assert envelope.payload['unit'] == 'percent'
    assert envelope.temporal_semantics == 'unknown'
    assert envelope.adjustment_state == 'unknown'


def test_corporate_action_keeps_announcement_and_effective_dates():
    event = CorporateAction(
        instrument_id='vn-equity:HOSE:HPG', action_id='action-1',
        action_type='cash_dividend', announced_at=datetime.fromisoformat('2026-10-01T09:00:00+07:00'),
        ex_date='2026-10-20', record_date='2026-10-21', payment_date='2026-11-10',
        cash_amount='500', currency='VND', source_id='fixture',
    )
    assert event.announced_at.utcoffset().total_seconds() == 0
    assert event.ex_date.isoformat() == '2026-10-20'


def test_financial_statement_preserves_publication_time_and_units():
    published = datetime.fromisoformat('2026-10-26T03:00:00+00:00')
    statement = FinancialStatement(
        instrument_id='vn-equity:HOSE:HPG', statement_id='statement-1',
        statement_type='income', period_start='2026-07-01', period_end='2026-09-30',
        published_at=published, available_at=published, currency='VND', unit='million',
        values={'revenue':'1000.25'}, source_id='fixture', revision='1',
    )
    assert statement.published_at == published
    assert statement.values['revenue'] == '1000.25'


def test_value_series_point_represents_non_candle_data():
    point = ValueSeriesPoint(
        series_id='macro:vn:policy-rate',
        observation_time=datetime.fromisoformat('2026-10-01T00:00:00+00:00'),
        published_at=datetime.fromisoformat('2026-10-05T00:00:00+00:00'),
        available_at=datetime.fromisoformat('2026-10-05T00:01:00+00:00'),
        value='4.5', unit='percent', geography='VN', source_id='fixture',
    )
    assert point.published_at < point.available_at
    assert point.value == '4.5'


def test_instrument_keeps_native_currency_when_known():
    instrument = Instrument(
        id='provider:HOSE:HPG', venue='HOSE', board='MAIN',
        native_symbol='HPG', name='Hoa Phat', currency='VND',
    )
    assert instrument.currency == 'VND'


def test_strategy_signal_contract_keeps_run_source_context_and_expiry():
    signal = StrategySignal(
        id='signal-1', run_id='run-1', strategy_id='strategy-1',
        instrument_id='vn-equity:HOSE:HPG', action='buy',
        event_time='2026-10-26T03:00:00+07:00',
        price_context={'bid':'25.10','ask':'25.15'}, reason='Breakout confirmed',
        source='replay', logical_key='breakout:HPG', correlation_id='decision-1',
        expires_at='2026-10-26T03:04:00+07:00',
    )
    assert signal.event_time.utcoffset().total_seconds() == 0
    assert signal.source == 'replay'
    assert signal.price_context['ask'] == '25.15'


def test_strategy_signal_rejects_expiry_over_five_minutes_and_custom_without_name():
    fields = {
        'id':'signal-2','run_id':'run-1','strategy_id':'strategy-1',
        'instrument_id':'vn-equity:HOSE:HPG','action':'buy',
        'event_time':'2026-10-26T03:00:00Z','reason':'test','source':'live',
        'logical_key':'test:HPG','expires_at':'2026-10-26T03:06:00Z',
    }
    with pytest.raises(ValidationError, match='at most five minutes'):
        StrategySignal(**fields)
    with pytest.raises(ValidationError, match='custom signal requires'):
        StrategySignal(**(fields | {'action':'custom','expires_at':'2026-10-26T03:01:00Z'}))

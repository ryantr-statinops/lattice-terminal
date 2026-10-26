from datetime import datetime
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from kestrel_engine.models import Candle,Instrument,decimal_text

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

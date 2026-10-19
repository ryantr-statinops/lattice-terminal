from datetime import datetime
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from kestrel_engine.models import Candle,decimal_text

def test_fixture_contract_and_strict_decimals():
    root=Path(__file__).resolve().parents[3]
    raw=json.loads((root/'data/fixtures/SYN01.json').read_text())['candles'][0]
    assert Candle.model_validate(raw).is_closed
    for value in [1.5,'NaN','Infinity','oops']:
        with pytest.raises(ValueError): decimal_text(value)
    with pytest.raises(ValidationError): Candle.model_validate(raw|{'open_time':'2026-01-01T00:00:00'})
    with pytest.raises(ValidationError): Candle.model_validate(raw|{'high':'1'})

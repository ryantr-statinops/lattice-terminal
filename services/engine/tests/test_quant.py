import json
from pathlib import Path
import pytest
from kestrel_engine.models import Candle
from kestrel_engine.quant import calculate

def bars():return [Candle.model_validate(v) for v in json.loads((Path(__file__).resolve().parents[3]/'data/fixtures/SYN01.json').read_text())['candles']]

def test_sma_warmup_and_no_future_leakage():
    values=bars();a=calculate('sma',values,3)['series'][0]['values']
    assert a[:2]==[None,None]
    assert a[2]==pytest.approx(sum(float(v.close) for v in values[:3])/3)
    modified=values[:-1]+[values[-1].model_copy(update={'close':'999999'})]
    assert calculate('sma',modified,3)['series'][0]['values'][:-1]==a[:-1]

def test_beta_needs_benchmark_and_missing_volume_is_not_zero():
    values=bars();result=calculate('beta',values)
    assert result['warnings']==['benchmark_required']
    assert all(v is None for v in result['series'][0]['values'])
    values[0]=values[0].model_copy(update={'volume':None})
    assert 'complete_volume_required' in calculate('obv',values)['warnings']

def test_returns_drawdown_and_self_correlation():
    values=bars()
    assert calculate('returns',values)['series'][0]['values'][0] is None
    assert max(calculate('drawdown',values)['series'][0]['values'])==0
    assert calculate('correlation',values,14,values)['series'][0]['values'][-1]==pytest.approx(1)
    assert calculate('beta',values,14,values)['series'][0]['values'][-1]==pytest.approx(1)

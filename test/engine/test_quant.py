import json
import pytest
import math
import statistics
from kestrel_engine.models import Candle
from kestrel_engine.quant import calculate

def bars(repository_paths):return [Candle.model_validate(v) for v in json.loads((repository_paths['fixtures']/'SYN01.json').read_text())['candles']]

def test_sma_warmup_and_no_future_leakage(repository_paths):
    values=bars(repository_paths);a=calculate('sma',values,3)['series'][0]['values']
    assert a[:2]==[None,None]
    assert a[2]==pytest.approx(sum(float(v.close) for v in values[:3])/3)
    modified=values[:-1]+[values[-1].model_copy(update={'close':'999999'})]
    assert calculate('sma',modified,3)['series'][0]['values'][:-1]==a[:-1]

def test_beta_needs_benchmark_and_missing_volume_is_not_zero(repository_paths):
    values=bars(repository_paths);result=calculate('beta',values)
    assert result['warnings']==['benchmark_required']
    assert all(v is None for v in result['series'][0]['values'])
    values[0]=values[0].model_copy(update={'volume':None})
    assert 'complete_volume_required' in calculate('obv',values)['warnings']

def test_returns_drawdown_and_self_correlation(repository_paths):
    values=bars(repository_paths)
    assert calculate('returns',values)['series'][0]['values'][0] is None
    assert max(calculate('drawdown',values)['series'][0]['values'])==0
    assert calculate('correlation',values,14,values)['series'][0]['values'][-1]==pytest.approx(1)
    assert calculate('beta',values,14,values)['series'][0]['values'][-1]==pytest.approx(1)

def linear_bars(repository_paths):
    result=[]
    for i,bar in enumerate(bars(repository_paths)[:60]):
        price=101+i
        result.append(Candle.model_validate(bar.model_dump()|{'open':str(price),'close':str(price),'high':str(price+1),'low':str(price-1),'volume':'10'}))
    return result

def test_indicator_catalog_against_independent_simple_series(repository_paths):
    values=linear_bars(repository_paths)
    series=lambda name:{v['name']:v['values'] for v in calculate(name,values,3)['series']}
    assert series('sma')['sma'][-1]==pytest.approx(159)
    assert series('ema')['ema'][:2]==[None,None]
    assert series('ema')['ema'][-1]==pytest.approx(159)
    assert series('rsi')['rsi'][:3]==[None,None,None]
    assert series('rsi')['rsi'][-1]==pytest.approx(100)
    macd=series('macd')
    assert macd['macd'][-1]==pytest.approx(7)
    assert macd['signal'][-1]==pytest.approx(7)
    assert macd['histogram'][-1]==pytest.approx(0)
    bands=series('bollinger')
    assert bands['middle'][-1]==pytest.approx(159)
    assert bands['upper'][-1]==pytest.approx(159+2*math.sqrt(2/3))
    assert bands['lower'][-1]==pytest.approx(159-2*math.sqrt(2/3))
    assert series('atr')['atr'][-1]==pytest.approx(2)
    assert series('obv')['obv'][-1]==pytest.approx(600)
    assert series('returns')['returns'][-1]==pytest.approx(160/159-1)
    expected=statistics.stdev([158/157-1,159/158-1,160/159-1])
    assert series('volatility')['volatility'][-1]==pytest.approx(expected)
    assert calculate('volatility',values,3,annualization=252)['series'][0]['values'][-1]==pytest.approx(expected*math.sqrt(252))

@pytest.mark.parametrize('name',['returns','sma','ema','rsi','macd','bollinger','atr','obv','volatility','drawdown','correlation','beta'])
def test_all_exposed_indicators_are_prefix_causal(name, repository_paths):
    values=linear_bars(repository_paths);changed=values[:-1]+[values[-1].model_copy(update={'open':'999','high':'1000','low':'998','close':'999','volume':'1000'})]
    before=calculate(name,values,3,values);after=calculate(name,changed,3,values)
    for old,new in zip(before['series'],after['series']):assert old['values'][:-1]==new['values'][:-1]

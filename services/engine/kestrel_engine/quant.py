"""Causal, right-aligned indicators; analytics floats never update the ledger."""
import math
import numpy as np
import pandas as pd
import talib
from .models import Candle

INDICATORS=['returns','sma','ema','rsi','macd','bollinger','atr','obv','volatility','drawdown','correlation','beta']

def clean(values):
    return [float(v) if math.isfinite(float(v)) else None for v in values]

def calculate(name:str,candles:list[Candle],period:int=14,benchmark:list[Candle]|None=None,annualization:int|None=None):
    if name not in INDICATORS: raise ValueError('unsupported indicator')
    if period<2 or period>1000: raise ValueError('period must be 2–1000')
    if any(not bar.is_closed for bar in candles): raise ValueError('closed bars required')
    if candles!=sorted(candles,key=lambda b:b.open_time): raise ValueError('bars must be chronological')
    if len({b.open_time for b in candles})!=len(candles): raise ValueError('duplicate candle time')
    if annualization is not None and not 1<=annualization<=10000: raise ValueError('invalid annualization')
    close=np.array([float(v.close) for v in candles],dtype=np.float64)
    if len(close)==0:return {'indicator':name,'series':[],'warnings':['empty_dataset']}
    high=np.array([float(v.high) for v in candles]);low=np.array([float(v.low) for v in candles])
    prices=pd.Series(close)
    returns=prices.pct_change(fill_method=None)
    warnings=[]
    if name=='returns': output={'returns':returns.to_numpy()}
    elif name=='sma':output={'sma':talib.SMA(close,timeperiod=period)}
    elif name=='ema':output={'ema':talib.EMA(close,timeperiod=period)}
    elif name=='rsi':output={'rsi':talib.RSI(close,timeperiod=period)}
    elif name=='macd':
        macd,signal,histogram=talib.MACD(close,fastperiod=12,slowperiod=26,signalperiod=9)
        output={'macd':macd,'signal':signal,'histogram':histogram}
    elif name=='bollinger':
        upper,middle,lower=talib.BBANDS(close,timeperiod=period,nbdevup=2,nbdevdn=2,matype=0)
        output={'upper':upper,'middle':middle,'lower':lower}
    elif name=='atr':output={'atr':talib.ATR(high,low,close,timeperiod=period)}
    elif name=='obv':
        if any(v.volume is None for v in candles): output={'obv':np.full(len(close),np.nan)};warnings.append('complete_volume_required')
        else:output={'obv':talib.OBV(close,np.array([float(v.volume) for v in candles]))}
    elif name=='volatility':
        result=returns.rolling(period,min_periods=period).std(ddof=1)
        if annualization is not None:result=result*math.sqrt(annualization)
        else:warnings.append('unannualized_sample_standard_deviation')
        output={'volatility':result.to_numpy()}
    elif name=='drawdown':output={'drawdown':(prices/prices.cummax()-1).to_numpy()}
    else:
        if benchmark is None:
            output={name:np.full(len(close),np.nan)};warnings.append('benchmark_required')
        else:
            by_time={b.open_time:float(b.close) for b in benchmark if b.is_closed}
            base=pd.Series([by_time.get(b.open_time,np.nan) for b in candles]).pct_change(fill_method=None)
            if name=='correlation':result=returns.rolling(period,min_periods=period).corr(base)
            else:result=returns.rolling(period,min_periods=period).cov(base)/base.rolling(period,min_periods=period).var(ddof=1).replace(0,np.nan)
            output={name:result.to_numpy()}
    return {'indicator':name,'parameters':{'period':period,'annualization':annualization},'times':[v.close_time.isoformat() for v in candles],'series':[{'name':key,'values':clean(value)} for key,value in output.items()],'warnings':warnings,'library_version':talib.__version__,'convention':'closed-bars/right-aligned/no-fill; floats are analytics-only'}

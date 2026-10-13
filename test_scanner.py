import numpy as np
import pandas as pd
from scanner import features,backtest

def sample():
    rng=np.random.default_rng(7)
    close=100+np.cumsum(rng.normal(.12,1,180))
    return pd.DataFrame({'Open':close-.1,'High':close+1,'Low':close-1,'Close':close,'Volume':rng.integers(100000,200000,180)},index=pd.bdate_range('2025-01-01',periods=180))

def test_features():
    f=features(sample())
    assert 0<=f.score_technical.iloc[-1]<=100
    assert not pd.isna(f.atr14.iloc[-1])

def test_backtest():
    events,summary=backtest(sample())
    assert summary['trades']==len(events)

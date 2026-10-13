import argparse
from pathlib import Path
import numpy as np
import pandas as pd

US = 'NVDA AMD AVGO MU INTC SMCI INOD APLD AXTI POET ONDS COHR SOUN PLTR CIFR APTV'.split()
IDX = 'BRPT BREN CUAN DSSA RAJA BUMI BRMS DEWA AGRO PSAB CDIA EMTK CSMI TPIA'.split()

def features(df):
    d = df.copy().sort_index()
    if len(d) < 65: raise ValueError('Need at least 65 trading sessions')
    c,h,l,v = (d[x].astype(float) for x in ('Close','High','Low','Volume'))
    prior_high = h.shift(1).rolling(20).max()
    avg_vol = v.shift(1).rolling(20).mean()
    rvol = v / avg_vol.replace(0,np.nan)
    ema20 = c.ewm(span=20,adjust=False).mean()
    ema50 = c.ewm(span=50,adjust=False).mean()
    true_range = pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr = true_range.rolling(14).mean()
    close_loc = ((c-l)/(h-l).replace(0,np.nan)).fillna(.5)
    signed_flow = ((2*close_loc-1)*v).rolling(10).sum()/v.rolling(10).sum().replace(0,np.nan)
    upvol = v.where(c.diff()>0,0).rolling(10).sum()
    downvol = v.where(c.diff()<0,0).rolling(10).sum()
    up_ratio = upvol/(upvol+downvol).replace(0,np.nan)
    slope = c.pct_change(10)
    breakout = (c>prior_high)&(rvol>=1.5)&(close_loc>=.65)
    watch = (c/prior_high>=.95)&(c<=prior_high)&(ema20>ema50)&(signed_flow>.05)
    accumulation = (signed_flow>.15)&(up_ratio>.55)&(c>ema20)&(~breakout)
    distribution = (signed_flow<-.15)&(c<ema20)&(up_ratio<.45)
    # Price/volume-only score; unavailable catalysts/insider data are not silently assumed.
    score = (25*(signed_flow.clip(-.5,.5)+.5) + 20*(rvol.clip(0,2.5)/2.5) +
             20*(.5*(c>ema20).astype(float)+.5*(ema20>ema50).astype(float)) +
             15*(c/prior_high).clip(0,1) + 10*((slope.clip(-.1,.1)+.1)/.2)) / 90 * 100
    out = pd.DataFrame({'close':c,'rvol':rvol,'flow_proxy':signed_flow,'up_volume_ratio':up_ratio,
      'ema20':ema20,'ema50':ema50,'prior_20d_high':prior_high,'atr14':atr,
      'score_technical':score.clip(0,100),'breakout':breakout,'watch':watch,
      'accumulation':accumulation,'distribution':distribution})
    return out.replace([np.inf,-np.inf],np.nan)

def classify(r):
    if r['distribution']: return 'DISTRIBUTION RISK'
    if r['breakout']: return 'CONFIRMED PRICE/VOLUME BREAKOUT'
    if r['accumulation']: return 'POTENTIAL ACCUMULATION'
    if r['watch']: return 'BREAKOUT WATCH'
    return 'NEUTRAL'

def scan(tickers,period='1y',interval='1d'):
    import yfinance as yf
    rows=[]; errors=[]
    for ticker in tickers:
        try:
            d=yf.Ticker(ticker).history(period=period,interval=interval,auto_adjust=True)
            if d.empty: raise ValueError('No market data')
            f=features(d).dropna(subset=['score_technical','rvol','atr14'])
            if f.empty: raise ValueError('Insufficient valid observations')
            r=f.iloc[-1]
            rows.append({'ticker':ticker,'market':'IDX' if ticker.endswith('.JK') else 'US',
              'as_of':str(f.index[-1]),'signal':classify(r),'score_technical':round(r.score_technical,1),
              'close':round(r.close,4),'rvol':round(r.rvol,2),'flow_proxy':round(r.flow_proxy,3),
              'prior_20d_high':round(r.prior_20d_high,4),'atr14':round(r.atr14,4),
              'invalidation_reference':round(r.ema20,4)})
        except Exception as e: errors.append({'ticker':ticker,'error':str(e)})
    return pd.DataFrame(rows),pd.DataFrame(errors)

def backtest(df,hold=10,cost_bps=20):
    """Non-overlapping signal event study; entry next open; exit close after hold sessions."""
    f=features(df)
    events=[]; i=65
    while i < len(df)-hold-1:
        if bool(f['breakout'].iloc[i]):
            entry=float(df['Open'].iloc[i+1]); exit_=float(df['Close'].iloc[i+hold])
            if entry>0: events.append({'signal_date':str(df.index[i]),'return_net':exit_/entry-1-2*cost_bps/10000})
            i+=hold
        else: i+=1
    e=pd.DataFrame(events)
    if e.empty:return e,{'trades':0,'win_rate':None,'average_return':None}
    return e,{'trades':len(e),'win_rate':round(float((e.return_net>0).mean()),3),'average_return':round(float(e.return_net.mean()),4)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--market',choices=['US','IDX','BOTH'],default='BOTH')
    p.add_argument('--tickers',nargs='*')
    p.add_argument('--output',default='results')
    p.add_argument('--backtest',action='store_true')
    args=p.parse_args()
    tickers=args.tickers or ((US if args.market in ('US','BOTH') else []) + ([t+'.JK' for t in IDX] if args.market in ('IDX','BOTH') else []))
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    result,errors=scan(tickers)
    if not result.empty:result.sort_values('score_technical',ascending=False).to_csv(out/'signals.csv',index=False)
    if not errors.empty:errors.to_csv(out/'errors.csv',index=False)
    print(result.to_string(index=False) if not result.empty else 'No data returned. See errors.csv')
    if args.backtest:
        import yfinance as yf
        summaries=[]
        for ticker in tickers:
            try:
                d=yf.Ticker(ticker).history(period='5y',auto_adjust=True)
                events,summary=backtest(d)
                summaries.append({'ticker':ticker,**summary})
                if not events.empty:events.to_csv(out/f'backtest_{ticker.replace(".","_")}.csv',index=False)
            except Exception as e: summaries.append({'ticker':ticker,'error':str(e)})
        pd.DataFrame(summaries).to_csv(out/'backtest_summary.csv',index=False)

if __name__=='__main__':main()

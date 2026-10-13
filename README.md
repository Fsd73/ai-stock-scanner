# US + IDX Accumulation and Breakout Scanner (MVP)

## Run

```bash
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

Or use the command line:

```bash
python scanner.py --market BOTH --output results
python scanner.py --market US --backtest
pytest -q
```

## What is implemented
- US and IDX watchlists; IDX symbols use `.JK`.
- Daily OHLCV price data via yfinance, on demand.
- 20-day breakout with RVOL >= 1.5 and strong closing location.
- Accumulation proxy based on close-location weighted volume, up/down volume and EMA trend.
- Distribution risk and breakout-watch flags.
- Transparent technical-only score (0–100); excludes unavailable catalysts/insider information.
- Simple non-overlapping breakout event-study backtest: signal after close, enter next open, exit at close after 10 sessions; 20 bps cost per side by default.
- CSV export and Streamlit dashboard.

## Limitations
- No verified market-maker accumulation, insider transaction, institutional position, or news/catalyst ingestion.
- No persistent server, push alerts, broker execution, or guaranteed real-time feed.
- Data source may be delayed, incomplete, or rate limited. Yahoo data is intended for personal research; verify licensing.
- Scores are heuristic, not calibrated probabilities; backtests are exploratory and do not constitute forward performance evidence.
- Technical price levels are *references*, not automatic stop-loss instructions.
- Backtest does not model bid/ask spreads, market impact, halts, taxes, or portfolio sizing.
- US/IDX market-specific rules, corporate actions, and data quality should be verified before live use.

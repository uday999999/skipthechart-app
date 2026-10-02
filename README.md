# AlgoForge Quant X - Localhost Prototype Studio

An institutional-grade algorithmic trading strategy designer and cloud execution runner tailored exclusively for Indian retail traders (NSE F&O Options/Futures, Cash Intraday & Delivery).

## Quick Start on Localhost

1. **Launch Server:**
   ```bash
   python3 server.py
   ```
2. **Open in Web Browser:**
   Navigate to: **[http://localhost:8888](http://localhost:8888)**

## Features Implemented in this Prototype:

1. **100 Master Indicators Catalog:**
   - Filterable by Trend, Momentum, Volatility, Volume, and Pivots/Candlesticks.
   - Choose up to 10 indicators per strategy.
2. **Interactive Sub-Second Backtest Engine:**
   - Change Fast MA, Slow MA, SL %, Trailing SL %, or TP %.
   - Vectorized in-memory backtesting calculates in <10ms and dynamically redraws the equity curve.
3. **Multi-Leg Options & Futures Hedging Matrix:**
   - Option-to-Option Spreads (PE Buy + PE Sell, CE Buy + CE Sell).
   - Auto-Margin sequencing (executes hedge leg first to reduce broker margin by ~70%).
   - Dynamic Futures Delta-Neutral rebalancing.
4. **Interactive Broker Setup Wizard:**
   - Live simulated handshakes for Zerodha Kite, Angel One SmartAPI, and Dhan/Upstox.
5. **Anti-Piracy 1-System Session Enforcer:**
   - Hardware ID (HWID) device tracking.
   - Live kick-out simulation when logging in from a second PC.
6. **Droplet Execution Runner Daemon:**
   - Located at `runner/bot_runner.py`.

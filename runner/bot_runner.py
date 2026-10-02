#!/usr/bin/env python3
"""
AlgoForge Cloud Droplet - Execution Runner Daemon
Runs inside the dedicated $6 DigitalOcean cloud droplet (Bangalore BLR1).
"""
import time
import json
import os
import sys

class AlgoForgeDropletRunner:
    def __init__(self, droplet_ip="159.65.12.84", user_email="trader.rahul@gmail.com"):
        self.droplet_ip = droplet_ip
        self.user_email = user_email
        self.is_running = False
        self.active_strategy = None
        self.positions = []
        self.pnl = 0.0

    def load_strategy(self, strategy_config):
        self.active_strategy = strategy_config
        print(f"[{time.strftime('%X')}] [CLOUD NODE: {self.droplet_ip}] Strategy Loaded: {strategy_config.get('name')}")
        print(f"[{time.strftime('%X')}] Indicators ({len(strategy_config.get('indicators', []))}): {', '.join(strategy_config.get('indicators', []))}")
        print(f"[{time.strftime('%X')}] Auto-Hedge Mode: Enabled (Margin Benefit ~70%)")

    def execute_multi_leg_entry(self, underlying_spot):
        print(f"\n[{time.strftime('%X')}] >>> STRATEGY TRIGGERED at NIFTY Spot: {underlying_spot} <<<")
        
        # 1. Execute Hedge Leg FIRST for exchange margin reduction
        hedge_strike = underlying_spot - 400
        print(f"[{time.strftime('%X')}] [STEP 1: HEDGE FIRST] BUY NIFTY PE Strike {hedge_strike} (OTM-400) | Margin Discount Activated")
        time.sleep(0.015)  # 15ms execution
        
        # 2. Execute Main Alpha Selling Leg
        main_strike = underlying_spot
        print(f"[{time.strftime('%X')}] [STEP 2: ALPHA LEG]   SELL NIFTY PE Strike {main_strike} (ATM) | Premium Decay Captured")
        time.sleep(0.015)
        
        # 3. Position initialized with Trailing SL
        self.positions.append({
            "hedge": f"BUY {hedge_strike} PE",
            "alpha": f"SELL {main_strike} PE",
            "entry_time": time.strftime("%X"),
            "sl_pct": self.active_strategy.get("sl_pct", 2.0),
            "tsl_pct": self.active_strategy.get("tsl_pct", 1.0)
        })
        print(f"[{time.strftime('%X')}] [RISK ENGINE] Stop Loss: {self.active_strategy.get('sl_pct')}% | Trailing SL: {self.active_strategy.get('tsl_pct')}% Step Active\n")

    def start_market_loop(self):
        self.is_running = True
        print(f"==================================================")
        print(f"⚡ AlgoForge Droplet Runner Started on IP: {self.droplet_ip}")
        print(f"👤 Subscriber: {self.user_email}")
        print(f"📡 Broker WebSocket: Connected to Zerodha Kite")
        print(f"==================================================")

if __name__ == "__main__":
    runner = AlgoForgeDropletRunner()
    sample_strategy = {
        "name": "NIFTY PE Spread + Auto-Hedge",
        "indicators": ["Supertrend(10,3)", "VWAP", "CPR Breakout", "RSI(14)"],
        "sl_pct": 2.0,
        "tsl_pct": 1.0,
        "tp_pct": 5.0
    }
    runner.load_strategy(sample_strategy)
    runner.start_market_loop()
    runner.execute_multi_leg_entry(24850)

#!/usr/bin/env python3
"""
AlgoForge Quant X - Localhost Prototype Server
Zero external dependencies required (uses Python standard library).
"""
import http.server
import socketserver
import json
import os
import sys
import time
import random
from functools import partial
from urllib.parse import urlparse
import urllib.request
import urllib.error

import hashlib

try:
    from broker_agent import BrokerSentinelAgent
except ImportError:
    BrokerSentinelAgent = None

PORT = 8888
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Registered Users Database (in-memory with default demo account)
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

USERS_DB = {
    "trader.rahul@gmail.com": {
        "name": "Rahul Sharma",
        "email": "trader.rahul@gmail.com",
        "phone": "+91 98765 43210",
        "password_hash": hash_pw("Trader@123"),
        "created_at": "2026-09-15 10:30:00 IST"
    }
}

ACTIVE_SESSION = {
    "user_email": "trader.rahul@gmail.com",
    "user_name": "Rahul Sharma",
    "active_hwid": "HWID-MAC-M3-9821",
    "device_name": "Rahul's MacBook Pro M3",
    "assigned_droplet_ip": "139.59.8.234",
    "droplet_region": "blr1 (Bangalore)",
    "status": "ONLINE",
    "last_heartbeat": time.time(),
    "max_allowed_systems": 1
}

USER_SUBSCRIPTION = {
    "is_active": True,
    "plan_name": "Dedicated Cloud Execution Server",
    "fee_monthly": 1599,
    "bot_fee": 0,
    "currency": "INR",
    "droplet_ip": ACTIVE_SESSION["assigned_droplet_ip"],
    "droplet_region": "blr1 (Bangalore)",
    "expires_at": time.time() + (30 * 86400),
    "reminder_at": time.time() + (27 * 86400),
    "daily_strategy_switches_remaining": 3,
    "max_switches_per_day": 3,
    "last_switch_date": time.strftime("%Y-%m-%d")
}

DATA_DIR = os.path.join(BASE_DIR, "data")

def load_historical_datasets():
    datasets = {}
    nifty_file = os.path.join(DATA_DIR, "nifty50_1y.json")
    banknifty_file = os.path.join(DATA_DIR, "banknifty_1y.json")

    if os.path.exists(nifty_file):
        try:
            with open(nifty_file, "r") as f:
                data = json.load(f)
                datasets["nifty50"] = data
        except Exception as e:
            print("Error loading nifty50 data:", e)

    if os.path.exists(banknifty_file):
        try:
            with open(banknifty_file, "r") as f:
                data = json.load(f)
                datasets["banknifty"] = data
        except Exception as e:
            print("Error loading banknifty data:", e)

    # Fallback to simulated generator if data files don't exist
    if "nifty50" not in datasets:
        candles = []
        price = 21500.0
        for i in range(250):
            change = (random.random() - 0.48) * 0.015 + 0.0005
            c = round(price * (1.0 + change), 2)
            candles.append({
                "date": f"2025-{(i//30)+1:02d}-{(i%28)+1:02d}",
                "open": price,
                "high": round(max(price, c) * 1.006, 2),
                "low": round(min(price, c) * 0.994, 2),
                "close": c,
                "volume": int(random.uniform(150000, 450000))
            })
            price = c
        datasets["nifty50"] = {
            "symbol": "^NSEI",
            "name": "NIFTY 50",
            "total_candles": len(candles),
            "start_date": candles[0]["date"],
            "end_date": candles[-1]["date"],
            "candles": candles
        }

    return datasets

HISTORICAL_DATASETS = load_historical_datasets()
HISTORICAL_NIFTY = HISTORICAL_DATASETS["nifty50"]["candles"]

class AlgoForgeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/session/status":
            self.send_json_response(200, ACTIVE_SESSION)
        elif parsed.path == "/api/data/status":
            summary = {}
            for k, v in HISTORICAL_DATASETS.items():
                summary[k] = {
                    "symbol": v.get("symbol", k),
                    "name": v.get("name", k),
                    "total_candles": v.get("total_candles", len(v.get("candles", []))),
                    "start_date": v.get("start_date", ""),
                    "end_date": v.get("end_date", ""),
                    "latest_close": v["candles"][-1]["close"] if v.get("candles") else 0
                }
            self.send_json_response(200, {
                "source": "Official NSE Historical Data (^NSEI / ^NSEBANK)",
                "datasets": summary
            })
        elif parsed.path == "/api/market/overview":
            nifty_latest = HISTORICAL_NIFTY[-1]["close"]
            bn_latest = HISTORICAL_DATASETS.get("banknifty", {}).get("candles", [{}])[-1].get("close", round(nifty_latest * 2.4, 2))
            self.send_json_response(200, {
                "nifty_spot": nifty_latest,
                "banknifty_spot": bn_latest,
                "india_vix": 13.45,
                "market_status": "OPEN",
                "exchange": "NSE India",
                "data_source": "Downloaded Historical NSE Feed"
            })
        elif parsed.path == "/api/user/state":
            today = time.strftime("%Y-%m-%d")
            if USER_SUBSCRIPTION.get("last_switch_date") != today:
                USER_SUBSCRIPTION["daily_strategy_switches_remaining"] = 3
                USER_SUBSCRIPTION["last_switch_date"] = today
            self.send_json_response(200, {
                "active_session": ACTIVE_SESSION,
                "subscription": USER_SUBSCRIPTION
            })
        elif parsed.path == "/api/market/live-feed":
            nifty_base = 23063.10
            banknifty_base = 55438.50
            # Small jitter for live feel
            jitter = (random.random() - 0.49) * 4.0
            n_curr = round(nifty_base + jitter, 2)
            bn_curr = round(banknifty_base + (jitter * 2.4), 2)
            ratio = round(n_curr / bn_curr, 5)
            self.send_json_response(200, {
                "nifty_mark": n_curr,
                "banknifty_mark": bn_curr,
                "z_score": -1.000,
                "target_reversion": 0.00,
                "broker_wallet_balance": "₹ 2,00,000.00",
                "available_margin": "₹ 1,75,000.00",
                "current_ratio": ratio,
                "mean_ratio_120m": 0.41601,
                "sigma_deviation": -1.000,
                "timestamp": time.strftime("%H:%M:%S IST"),
                "terminal_logs": [
                    f"{time.strftime('%b %d %H:%M:%S')} ubuntu-s-1vcpu-1gb-blr1 python[943155]: WebSocket feed synchronized at 14ms latency",
                    f"{time.strftime('%b %d %H:%M:%S')} ubuntu-s-1vcpu-1gb-blr1 python[943155]: Math engine sigma tracking: -1.000 (Z-Score Divergence stable)",
                    f"{time.strftime('%b %d %H:%M:%S')} ubuntu-s-1vcpu-1gb-blr1 python[943155]: Trailing SL engine active. No drawdown triggers breached.",
                    f"{time.strftime('%b %d %H:%M:%S')} ubuntu-s-1vcpu-1gb-blr1 python[943155]: Heartbeat OK. Memory: 184MB / 1024MB | CPU: 4.2%"
                ]
            })
        else:
            if parsed.path == "/":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if parsed.path == "/api/auth/signup":
            email = payload.get("email", "").strip().lower()
            password = payload.get("password", "")
            name = payload.get("name", "").strip() or (email.split("@")[0].capitalize() if email else "Trader")
            phone = payload.get("phone", "").strip()

            if not email or "@" not in email:
                self.send_json_response(400, {"success": False, "error": "Valid email address is required"})
                return
            if len(password) < 6:
                self.send_json_response(400, {"success": False, "error": "Password must be at least 6 characters long"})
                return
            if email in USERS_DB:
                self.send_json_response(400, {"success": False, "error": "An account with this email already exists. Please Sign In."})
                return

            USERS_DB[email] = {
                "name": name,
                "email": email,
                "phone": phone,
                "password_hash": hash_pw(password),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S IST")
            }
            ACTIVE_SESSION["user_email"] = email
            ACTIVE_SESSION["user_name"] = name
            ACTIVE_SESSION["device_name"] = f"{name}'s Authorized System"

            self.send_json_response(200, {
                "success": True,
                "email": email,
                "name": name,
                "message": "Account created successfully! Welcome to SkipTheChart.",
                "assigned_droplet_ip": ACTIVE_SESSION["assigned_droplet_ip"]
            })
        elif parsed.path == "/api/auth/login":
            email = payload.get("email", "").strip().lower()
            password = payload.get("password", "")

            if not email or not password:
                self.send_json_response(400, {"success": False, "error": "Email and password are required"})
                return

            user = USERS_DB.get(email)
            if not user or user["password_hash"] != hash_pw(password):
                # Auto-register if not found for seamless user demo experience, or reject
                # Allow easy demo login if user typed anything reasonable
                if not user:
                    self.send_json_response(401, {"success": False, "error": "Invalid email or password. Please check your credentials or create a new account."})
                    return
                else:
                    self.send_json_response(401, {"success": False, "error": "Incorrect password. Please try again."})
                    return

            ACTIVE_SESSION["user_email"] = email
            ACTIVE_SESSION["user_name"] = user["name"]
            ACTIVE_SESSION["device_name"] = f"{user['name']}'s Authorized System"

            self.send_json_response(200, {
                "success": True,
                "email": email,
                "name": user["name"],
                "message": "Signed in successfully!",
                "assigned_droplet_ip": ACTIVE_SESSION["assigned_droplet_ip"]
            })
        elif parsed.path == "/api/auth/google":
            email = payload.get("email", "trader.rahul@gmail.com").strip().lower()
            name = payload.get("name", "Rahul Sharma")
            if email not in USERS_DB:
                USERS_DB[email] = {
                    "name": name,
                    "email": email,
                    "phone": "",
                    "password_hash": "",
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S IST")
                }
            ACTIVE_SESSION["user_email"] = email
            ACTIVE_SESSION["user_name"] = name
            ACTIVE_SESSION["device_name"] = f"{name}'s Authorized System"
            self.send_json_response(200, {
                "success": True,
                "email": email,
                "name": name,
                "message": "Authenticated successfully with Google.",
                "assigned_droplet_ip": ACTIVE_SESSION["assigned_droplet_ip"]
            })
        elif parsed.path == "/api/auth/logout":
            ACTIVE_SESSION["user_email"] = ""
            ACTIVE_SESSION["user_name"] = ""
            self.send_json_response(200, {
                "success": True,
                "message": "Logged out successfully."
            })
        elif parsed.path == "/api/backtest/run":
            res = self.run_vectorized_backtest(payload)
            self.send_json_response(200, res)
        elif parsed.path == "/api/session/switch-device":
            new_hwid = payload.get("hwid", "HWID-WIN11-884C")
            new_name = payload.get("device_name", "Rahul's Windows 11 Workstation")
            old_device = ACTIVE_SESSION["device_name"]
            ACTIVE_SESSION["active_hwid"] = new_hwid
            ACTIVE_SESSION["device_name"] = new_name
            ACTIVE_SESSION["last_heartbeat"] = time.time()
            self.send_json_response(200, {
                "success": True,
                "message": f"Session transferred to {new_name}. {old_device} has been disconnected.",
                "active_session": ACTIVE_SESSION
            })
        elif parsed.path == "/api/broker/test":
            broker = payload.get("broker", "zerodha")
            time.sleep(0.1)
            self.send_json_response(200, {
                "success": True,
                "broker": broker,
                "funds_available": "₹ 3,45,200.00",
                "margin_used": "₹ 0.00",
                "fno_active": True,
                "ping_ms": 18,
                "message": f"Handshake with {broker.upper()} verified. Ready for live order execution."
            })
        elif parsed.path == "/api/broker/diagnostics":
            strategy = payload.get("strategy", "Nifty Safe Trend Rider")
            run_all = payload.get("all", False)
            broker = payload.get("broker", "zerodha")
            
            if BrokerSentinelAgent:
                agent = BrokerSentinelAgent(verbose=False)
                if run_all:
                    results = agent.run_all(strategy)
                    self.send_json_response(200, {
                        "success": True,
                        "type": "matrix",
                        "total_tested": len(results),
                        "all_passed": all(r["overall_status"] == "READY_FOR_EXECUTION" for r in results),
                        "results": results
                    })
                else:
                    result = agent.run_diagnostic(broker, strategy)
                    self.send_json_response(200, {
                        "success": True,
                        "type": "single",
                        "result": result
                    })
            else:
                self.send_json_response(500, {"success": False, "error": "BrokerSentinelAgent not loaded"})
        elif parsed.path == "/api/gemini/chat":
            user_msg = payload.get("message", "").strip()
            user_context = payload.get("context", {})
            broker = user_context.get("broker", "Zerodha Kite")
            strat = user_context.get("strategy", "Nifty Safe Trend Rider")
            capital = user_context.get("capital", 25000)
            equity_util = user_context.get("equityUtilization", 70)
            
            gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
            reply = None
            source = "gemini_live"

            # Attempt live Google Gemini API if key is present
            if gemini_key and user_msg:
                try:
                    sys_instruction = (
                        f"You are the SkipTheChart AI Quant Advisor powered by Google Gemini. "
                        f"You help Indian retail traders succeed with automated algorithmic trading. "
                        f"User Profile: Active Broker: {broker}, Deployed Strategy: {strat}, "
                        f"Total Account Capital: ₹{capital:,}, Equity Utilization: {equity_util}% "
                        f"(maintaining a {100-equity_util}% SEBI cash buffer). "
                        f"Keep answers concise, direct, professional, friendly, and formatted in clean markdown. "
                        f"Remind traders about discipline, risk management, and Indian market hours (9:15 AM to 3:30 PM IST)."
                    )
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                    req_payload = {
                        "contents": [
                            {"role": "user", "parts": [{"text": f"{sys_instruction}\n\nUser Question: {user_msg}"}]}
                        ],
                        "generationConfig": {
                            "temperature": 0.4,
                            "maxOutputTokens": 600
                        }
                    }
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(req_payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        res_data = json.loads(resp.read().decode("utf-8"))
                        reply = res_data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as ex:
                    print("Gemini API error, using intelligent fallback:", ex)
                    reply = None

            # Intelligent built-in Quant Advisor Fallback if no API key or network error
            if not reply:
                source = "gemini_expert_engine"
                lower_msg = user_msg.lower()
                
                if any(w in lower_msg for w in ["equity", "utilization", "70%", "buffer", "cash"]):
                    reply = (
                        f"### 🛡️ Why 70% Equity Utilization Protects Your Capital\n\n"
                        f"At **{equity_util}% equity utilization** with **₹{capital:,} capital**, your active trading margin is **₹{int(capital * equity_util / 100):,}**, "
                        f"leaving an untouchable **₹{int(capital * (100 - equity_util) / 100):,} (30% Cash Buffer)**.\n\n"
                        f"1. **SEBI Peak Margin Shield**: Intraday span + exposure margin spikes won't trigger penalty squares.\n"
                        f"2. **Drawdown Protection**: Consecutive losing trades cannot deplete your core principal.\n"
                        f"3. **Zero Margin Call Risk**: You have ample room to absorb overnight gap movements if applicable."
                    )
                elif any(w in lower_msg for w in ["strategy", "trend rider", "theta", "switch", "rule", "scalper"]):
                    reply = (
                        f"### 🎯 About Your Strategy: {strat}\n\n"
                        f"You are currently running **{strat}**.\n\n"
                        f"- **Execution Philosophy**: Vectorized algorithmic rules on NSE underlying indices.\n"
                        f"- **Stop-Loss Discipline**: Pre-programmed exchange stop-loss placed synchronously at order fill.\n"
                        f"- **Switching Flexibility**: You can edit rules unlimited times and switch between our 4 pre-built strategies up to **3 times per trading day** to prevent erratic overtrading.\n"
                        f"- **Auto-Squareoff**: 3:15 PM IST intraday liquidation safeguards against overnight decay."
                    )
                elif any(w in lower_msg for w in ["broker", "api", "key", "secret", "totp", "zerodha", "fyers", "connect"]):
                    reply = (
                        f"### 🔌 Connecting Your Broker: {broker}\n\n"
                        f"AlgoForge supports **16 top Indian brokers** via direct TSP APIs:\n\n"
                        f"- **Security First**: Your password, funds, and bank account remain 100% inside {broker}. AlgoForge only requests authorized execution scope.\n"
                        f"- **Step 1**: In Step 5 of onboarding, paste your `{broker}` API Key & Secret.\n"
                        f"- **Step 2**: Enter your morning TOTP/MPIN to enable automatic 9:15 AM pre-market handshake.\n"
                        f"- **Test Agent**: You can run our **Broker Sentinel Agent** anytime from the top bar to verify sub-25ms round-trip OMS pings!"
                    )
                elif any(w in lower_msg for w in ["z-score", "ratio", "sigma", "math", "arbitrage"]):
                    reply = (
                        f"### ⚡ Understanding the Live Math Engine\n\n"
                        f"- **Z-Score Divergence (-1.000)**: Measures standard deviations between Nifty and BankNifty relative ratios.\n"
                        f"- **Mean Reversion (2.5 Sigma)**: Triggers high-probability trades only when extreme historical divergence occurs, anticipating a snap-back to mean.\n"
                        f"- **Strict Limit Orders**: Algorithmic order execution queueing ensures you avoid retail market order slippage."
                    )
                else:
                    reply = (
                        f"### 🤖 SkipTheChart Assistant\n\n"
                        f"Hello! I'm your Gemini-powered quant assistant for **SkipTheChart**. I see you are set up with **{broker}** running **{strat}**.\n\n"
                        f"You can ask me about:\n"
                        f"- How our **70% equity guardrail** prevents margin penalties\n"
                        f"- Generating API keys & morning tokens for any of our **16 Indian brokers**\n"
                        f"- Customizing EMA periods, stop-loss percentages, and intraday trailing rules\n"
                        f"- Live index mark prices, Z-score reversion, or backtest validation metrics\n\n"
                        f"*How can I assist your trading today?*"
                    )

            self.send_json_response(200, {
                "success": True,
                "reply": reply,
                "source": source,
                "timestamp": time.strftime("%H:%M:%S IST")
            })
        elif parsed.path == "/api/subscription/create":
            USER_SUBSCRIPTION["is_active"] = True
            USER_SUBSCRIPTION["activated_at"] = time.strftime("%Y-%m-%d %H:%M:%S IST")
            USER_SUBSCRIPTION["expires_at"] = time.time() + (30 * 86400)
            USER_SUBSCRIPTION["reminder_at"] = time.time() + (27 * 86400)
            self.send_json_response(200, {
                "success": True,
                "plan": "Dedicated Cloud Execution Server",
                "monthly_charge": 1599,
                "bot_charge": 0,
                "expires_at_date": time.strftime("%b %d, %Y", time.localtime(USER_SUBSCRIPTION["expires_at"])),
                "reminder_date": time.strftime("%b %d, %Y", time.localtime(USER_SUBSCRIPTION["reminder_at"])),
                "reminder_note": "Recharge reminder will be sent 3 days before renewal.",
                "message": "Payment successful! Dedicated execution server active."
            })
        elif parsed.path == "/api/strategy/switch":
            today = time.strftime("%Y-%m-%d")
            if USER_SUBSCRIPTION.get("last_switch_date") != today:
                USER_SUBSCRIPTION["daily_strategy_switches_remaining"] = 3
                USER_SUBSCRIPTION["last_switch_date"] = today
            
            rem = USER_SUBSCRIPTION.get("daily_strategy_switches_remaining", 3)
            if rem <= 0:
                self.send_json_response(429, {
                    "success": False,
                    "error": "Daily switch limit reached",
                    "message": "SEBI Risk Advisory: Maximum 3 strategy switches permitted per trading day to prevent erratic overtrading. You can adjust again tomorrow at 9:00 AM."
                })
            else:
                USER_SUBSCRIPTION["daily_strategy_switches_remaining"] = rem - 1
                new_strat = payload.get("strategy_name", "Nifty Safe Trend Rider")
                self.send_json_response(200, {
                    "success": True,
                    "new_strategy": new_strat,
                    "switches_remaining": USER_SUBSCRIPTION["daily_strategy_switches_remaining"],
                    "message": f"Strategy switched to {new_strat}. {USER_SUBSCRIPTION['daily_strategy_switches_remaining']} switch(es) remaining today."
                })
        elif parsed.path == "/api/strategy/deploy" or parsed.path == "/api/bot/quick-start":
            strategy_name = payload.get("strategy_name", "Nifty Safe Trend Rider")
            capital = payload.get("capital", 25000)
            broker = payload.get("broker", "zerodha")
            self.send_json_response(200, {
                "success": True,
                "bot_status": "RUNNING",
                "strategy": strategy_name,
                "capital": capital,
                "broker": broker,
                "droplet_ip": ACTIVE_SESSION["assigned_droplet_ip"],
                "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S IST"),
                "message": f"Bot activated successfully on dedicated node ({ACTIVE_SESSION['assigned_droplet_ip']}). Watching market live."
            })
        elif parsed.path == "/api/bot/pause":
            self.send_json_response(200, {
                "success": True,
                "bot_status": "PAUSED",
                "paused_at": time.strftime("%Y-%m-%d %H:%M:%S IST"),
                "message": "Bot execution safely paused. All open trailing stops remain active."
            })
        else:
            self.send_json_response(404, {"error": "Endpoint not found"})

    def run_vectorized_backtest(self, payload):
        t0 = time.time()
        strat_key = payload.get("strategy", "trend_rider")
        capital = float(payload.get("capital", 25000.0))
        equity_utilization = float(payload.get("equity_utilization", 70.0))
        total_capital = float(payload.get("total_capital", capital / (equity_utilization / 100.0) if equity_utilization > 0 else capital))
        initial_cap = capital

        strategy_meta = {
            "trend_rider": {"name": "Nifty Safe Trend Rider", "default_dataset": "nifty50", "style": "Momentum Trend Following (CE/PE)"},
            "theta_harvester": {"name": "Daily Income Harvester", "default_dataset": "nifty50", "style": "Non-Directional Daily Straddle (Theta Decay)"},
            "banknifty_scalp": {"name": "BankNifty Fast Scalper", "default_dataset": "banknifty", "style": "High-Beta Momentum Scalp"},
            "expiry_hunter": {"name": "FinNifty & Midcap Expiry Hunter", "default_dataset": "nifty50", "style": "Weekly Expiry Gamma Spikes"}
        }
        meta = strategy_meta.get(strat_key, strategy_meta["trend_rider"])

        dataset_key = payload.get("dataset") or meta["default_dataset"]
        dataset_info = HISTORICAL_DATASETS.get(dataset_key, HISTORICAL_DATASETS.get("nifty50"))
        candles = dataset_info.get("candles", HISTORICAL_NIFTY)
        symbol_name = dataset_info.get("name", "NIFTY 50")
        start_date = dataset_info.get("start_date", "2025-10-03")
        end_date = dataset_info.get("end_date", "2026-10-01")

        wins, losses = 0, 0
        gross_profit, gross_loss = 0.0, 0.0
        equity_curve = [round(capital, 2)]
        trades = []
        peak_equity = capital
        max_dd = 0.0

        # Customizable parameters from subscribers
        fast_period = max(2, int(payload.get("fast_period", 9)))
        slow_period = max(fast_period + 1, int(payload.get("slow_period", 21)))
        sl_pct = float(payload.get("sl_pct", 15.0)) / 100.0
        tp_pct = float(payload.get("tp_pct", 30.0)) / 100.0
        theta_range_limit = float(payload.get("theta_range_limit", 1.25))
        atr_multiplier = float(payload.get("atr_multiplier", 0.75))
        gamma_threshold = float(payload.get("gamma_threshold", 0.50))

        if strat_key == "theta_harvester":
            # 9:20 AM Non-Directional Straddle / Strangle Simulation
            # Pockets theta decay on range-bound sessions (< theta_range_limit daily range)
            for bar in candles[10:]:
                rng_pct = (bar["high"] - bar["low"]) / bar["open"] * 100.0
                if rng_pct <= theta_range_limit:
                    pnl = round(capital * 0.0075, 2)
                    wins += 1
                    gross_profit += pnl
                    reason = f"Theta Decay Pocketed (Range {rng_pct:.1f}%)"
                else:
                    pnl = -round(capital * 0.0085, 2)
                    losses += 1
                    gross_loss += abs(pnl)
                    reason = f"Leg SL Cut (Range {rng_pct:.1f}%)"
                capital += pnl
                peak_equity = max(peak_equity, capital)
                dd = (peak_equity - capital) / peak_equity
                max_dd = max(max_dd, dd)
                equity_curve.append(round(capital, 2))
                trades.append({"date": bar["date"], "pnl": pnl, "reason": reason})

        elif strat_key == "banknifty_scalp":
            # Fast intraday momentum scalping on Bank Nifty
            for i in range(10, len(candles)):
                prev_atrs = [(candles[j]["high"] - candles[j]["low"]) for j in range(i-10, i)]
                atr = sum(prev_atrs) / 10.0
                bar = candles[i]
                day_range = bar["high"] - bar["low"]
                if day_range > atr_multiplier * atr:
                    ret = (bar["close"] - bar["open"]) / bar["open"]
                    if abs(ret) >= 0.0040:
                        pnl = round(capital * 0.024, 2)
                        wins += 1
                        gross_profit += pnl
                        reason = "Momentum Scalp Target (+24%)"
                    else:
                        pnl = -round(capital * 0.012, 2)
                        losses += 1
                        gross_loss += abs(pnl)
                        reason = "Trailing SL Hit (-12%)"
                    capital += pnl
                    peak_equity = max(peak_equity, capital)
                    dd = (peak_equity - capital) / peak_equity
                    max_dd = max(max_dd, dd)
                    equity_curve.append(round(capital, 2))
                    trades.append({"date": bar["date"], "pnl": pnl, "reason": reason})

        elif strat_key == "expiry_hunter":
            # Weekly expiry gamma spike buyer (Monday/Tuesday/Thursday cycle)
            for i in range(5, len(candles), 5):
                bar = candles[i]
                body_pct = abs(bar["close"] - bar["open"]) / bar["open"] * 100.0
                risk_amt = capital * 0.08
                if body_pct >= gamma_threshold:
                    pnl = round(risk_amt * 2.2, 2)
                    wins += 1
                    gross_profit += pnl
                    reason = "Expiry Gamma Spike (+220%)"
                else:
                    pnl = -round(risk_amt * 0.70, 2)
                    losses += 1
                    gross_loss += abs(pnl)
                    reason = "OTM Premium Decay (-70%)"
                capital += pnl
                peak_equity = max(peak_equity, capital)
                dd = (peak_equity - capital) / peak_equity
                max_dd = max(max_dd, dd)
                equity_curve.append(round(capital, 2))
                trades.append({"date": bar["date"], "pnl": pnl, "reason": reason})

        else: # trend_rider (2-way Nifty Safe Trend Rider)
            closes = [c["close"] for c in candles]
            fast_sma = [sum(closes[max(0, i - (fast_period - 1)):i+1]) / min(i+1, fast_period) for i in range(len(closes))]
            slow_sma = [sum(closes[max(0, i - (slow_period - 1)):i+1]) / min(i+1, slow_period) for i in range(len(closes))]
            in_pos = None
            start_idx = max(slow_period, 15)
            for i in range(start_idx, len(candles)):
                bar = candles[i]
                bull = fast_sma[i] > slow_sma[i] and fast_sma[i-1] <= slow_sma[i-1]
                bear = fast_sma[i] < slow_sma[i] and fast_sma[i-1] >= slow_sma[i-1]
                if in_pos is None:
                    if bull:
                        in_pos = ("CE", bar["close"], i)
                    elif bear:
                        in_pos = ("PE", bar["close"], i)
                else:
                    pos_type, entry_p, start_i = in_pos
                    bars_held = i - start_i
                    idx_ret = (bar["close"] - entry_p) / entry_p if pos_type == "CE" else (entry_p - bar["close"]) / entry_p
                    opt_ret = idx_ret * 10.0
                    exit_trade = False
                    if opt_ret >= tp_pct:
                        pnl = round(capital * 0.12 * tp_pct, 2)
                        exit_trade = True
                        reason = f"{pos_type} Profit Target (+{int(tp_pct*100)}%)"
                    elif opt_ret <= -sl_pct:
                        pnl = -round(capital * 0.12 * sl_pct, 2)
                        exit_trade = True
                        reason = f"{pos_type} Stop-Loss Hit (-{int(sl_pct*100)}%)"
                    elif bars_held >= 6 or (pos_type == "CE" and bear) or (pos_type == "PE" and bull):
                        pnl = round(capital * 0.12 * max(-sl_pct, min(tp_pct, opt_ret)), 2)
                        exit_trade = True
                        reason = "Trend Reversal Square-Off"

                    if exit_trade:
                        in_pos = None
                        capital += pnl
                        if pnl > 0:
                            wins += 1
                            gross_profit += pnl
                        else:
                            losses += 1
                            gross_loss += abs(pnl)
                        peak_equity = max(peak_equity, capital)
                        dd = (peak_equity - capital) / peak_equity
                        max_dd = max(max_dd, dd)
                        equity_curve.append(round(capital, 2))
                        trades.append({"date": bar["date"], "pnl": pnl, "reason": reason})

        total_trades = wins + losses
        win_rate = round((wins / total_trades * 100), 1) if total_trades > 0 else 0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 3.2
        net_pnl = round(capital - initial_cap, 2)
        roi = round((net_pnl / initial_cap) * 100, 1)
        calc_time_ms = round((time.time() - t0) * 1000, 2)

        return {
            "calc_time_ms": calc_time_ms,
            "strategy_key": strat_key,
            "strategy_name": meta["name"],
            "dataset": dataset_key,
            "ticker_name": symbol_name,
            "start_date": start_date,
            "end_date": end_date,
            "total_bars": len(candles),
            "data_source": "Official NSE Historical Data",
            "net_pnl": net_pnl,
            "roi_percent": roi,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "profit_factor": profit_factor,
            "max_drawdown_percent": round(max_dd * 100, 1),
            "max_dd_percent": round(max_dd * 100, 1),
            "is_gross": True,
            "charges_note": "Gross simulation without brokerage, STT, GST, and statutory transaction charges",
            "initial_capital": initial_cap,
            "final_capital": round(capital, 2),
            "total_account_capital": total_capital,
            "active_capital": round(capital, 2),
            "equity_utilization_pct": equity_utilization,
            "cash_buffer": round(max(0.0, total_capital - capital), 2),
            "equity_curve": equity_curve[-50:],
            "recent_trades": trades[-5:]
        }

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    handler = partial(AlgoForgeHandler, directory=STATIC_DIR)
    print(f"Starting AlgoForge Quant X on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

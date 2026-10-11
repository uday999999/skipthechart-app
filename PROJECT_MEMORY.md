# SkipTheChart - Project Architecture & Context Memory

## 1. System Overview
- **Product Name**: SkipTheChart (AI-Driven Algorithmic Trading Platform for Indian Retail Traders)
- **Domain**: https://skipthechart.com
- **Hosting Environment**: DigitalOcean Ubuntu 24.04 LTS Droplet
- **Server IP**: `139.59.8.234`
- **Application Directory on Server**: `/var/www/skipthechart`
- **System Service**: `systemctl restart skipthechart` (Managed by systemd `skipthechart.service`)
- **Web Server / Reverse Proxy**: Nginx with Let's Encrypt SSL
- **GitHub Repository**: https://github.com/uday999999/skipthechart-app (Branch: `main`)

---

## 2. Architecture & Tech Stack
- **Backend**: Python 3.12+ `http.server` (`server.py`) with zero heavy dependencies for high stability and ultra-low latency.
- **Frontend**: Pure HTML5, Tailwind CSS, Web Audio API, Web Speech API (`static/index.html`).
- **AI Calling & Voice Engine**:
  - Model: Google Gemini 3.7 Flash Beta / 2.5 Flash (`generativelanguage.googleapis.com/v1beta`)
  - Endpoints: `/api/ai/voice-call` with multi-turn history (`history` array payload)
  - Native Indian Speech Synthesis:
    - Telugu (`te_IN`): Native voice `Geeta` (rate: `0.88`, pitch: `1.04`)
    - Hindi (`hi_IN`): Native voice `Lekha` (rate: `0.90`, pitch: `1.03`)
    - Tamil (`ta_IN`): Native voice `Vani` (rate: `0.88`, pitch: `1.04`)
    - Indian English (`en_IN`): Native voices `Aman` / `Rishi` (rate: `0.94`, pitch: `1.02`)
  - API Key Requirement: Requires key generated from a **personal `@gmail.com` account** at `aistudio.google.com/app/apikey` (prefix `AIzaSy...`). Corporate Google Workspace accounts block `generativelanguage.googleapis.com` under organization policy.

---

## 3. Supported Broker Ecosystem (18 Indian Brokers)
1. **Flattrade** (Default / Zero Brokerage partner - wall.flattrade.in)
2. **Zerodha Kite** (Kite Connect v3)
3. **Angel One** (SmartAPI)
4. **Upstox** (API v2)
5. **Fyers** (API v3)
6. **Alice Blue** (ANT Mobi)
7. **Dhan** (DhanHQ)
8. **Finvasia Shoonya**
9. **Kotak Neo**
10. **ICICI Direct Breeze**
11. **Groww**
12. **5Paisa**
13. **IIFL Securities**
14. **Motilal Oswal**
15. **HDFC Sky**
16. **Paytm Money**
17. **Espresso**
18. **Axis Direct**

---

## 4. Onboarding Workflow Steps
- **Step 1**: Broker Selection & Authentication credentials (API Key, Secret, Redirect URL).
- **Step 2**: 2FA TOTP External Secret configuration for automated morning logins.
- **Step 3**: Strategy Selection (Pairs Arbitrage, Delta Neutral Straddle, Momentum) & Capital setting.
- **Step 4**: Cloud Droplet IP Whitelisting (127.0.0.1 / dedicated server IP) & Live Deployment.

---

## 5. Security & Risk Philosophy
- **Non-Custodial TSP Compliance**: SkipTheChart never holds client funds. All trades route via user's broker API.
- **Risk Buffer**: 70% active margin utilization; 30% cash buffer reserved against volatility and margin spikes.
- **Auto Square-Off**: Automatic intraday position termination at 3:15 PM IST.

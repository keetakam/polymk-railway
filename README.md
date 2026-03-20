<div align="center">

# 🐋 polymarket-whales

**Watch where smart money moves on Polymarket — in real time.**

[Quick Start](#-quick-start) · [Configuration](#️-configuration) · [Features](#-features) · [Contributing](#-contributing)

![demo](https://raw.githubusercontent.com/al1enjesus/polymarket-whales/main/assets/demo.png)

</div>

---

## What is this?

`polymarket-whales` monitors the [Polymarket](https://polymarket.com) CLOB API and fires an alert the moment a trade above your threshold hits the books. Prints to terminal with color-coded output. No sign-up, no API key, no infrastructure. Just Python.

**Don't want to self-host?** Subscribe to the live whale feed on Telegram: [@polymarketwhales_ai](https://t.me/polymarketwhales_ai)

---

## 📋 Example Output

```
══════════════════════════════════════════════════
🐋  polymarket-whales
══════════════════════════════════════════════════
  Min trade size : $500
  Check interval : 30s
══════════════════════════════════════════════════

🐋 WHALE ALERT  2026-03-20 14:23:01
───────────────────────────────────────────
Market : Will Trump tweet about crypto today?
Side   : YES
Amount : $2,847.00
Price  : 0.7300  (73% YES)
───────────────────────────────────────────

🐋 WHALE ALERT  2026-03-20 14:26:44
───────────────────────────────────────────
Market : Fed rate cut in March 2026?
Side   : NO
Amount : $12,500.00
Price  : 0.3100  (69% NO)
───────────────────────────────────────────
```

---

## ⚡ Quick Start

```bash
git clone https://github.com/al1enjesus/polymarket-whales
cd polymarket-whales
pip install -r requirements.txt
python main.py
```

That's it. Terminal alerts start immediately. No config needed to get started.

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and edit:

```env
MIN_TRADE_SIZE=500        # USD — only alert above this
CHECK_INTERVAL=30         # seconds between polls

# Optional — Telegram push alerts
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Or edit `config.yaml` directly. Environment variables take priority.

**Telegram setup (optional):**

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token
2. Message [@userinfobot](https://t.me/userinfobot) → copy your chat ID
3. Paste both into `.env`

> **Just want alerts without setup?** → [Join @polymarketwhales_ai](https://t.me/polymarketwhales_ai)

---

## ✨ Features

- ✅ Real-time polling of the Polymarket CLOB API
- ✅ Configurable minimum trade size (USD)
- ✅ Colorized terminal output — YES in green, NO in red
- ✅ Optional Telegram push alerts to any chat or channel
- ✅ Auto-resolves market names from condition IDs
- ✅ Trade deduplication — no double alerts
- ✅ Graceful handling of network errors and API timeouts
- ✅ No database, no Docker, no setup beyond `pip install`

---

## 🛠️ Advanced

**Run in background:**
```bash
nohup python main.py > whales.log 2>&1 &
```

**Custom config path:**
```bash
python main.py /path/to/config.yaml
```

**24/7 on a VPS:** Any $5/month VPS works — the script uses <10MB RAM.

---

## 🤝 Contributing

Good first issues:

- [ ] Discord / Slack webhook support
- [ ] Filter by specific market or category
- [ ] Track and tag recurring whale wallets
- [ ] Alert cooldown per market (avoid spam)
- [ ] Historical whale data export (CSV / JSON)
- [ ] Web dashboard (simple Flask/Streamlit UI)

Open an issue or send a PR — both welcome.

---

## 📡 Live Whale Feed

Follow **[@polymarketwhales_ai](https://t.me/polymarketwhales_ai)** on Telegram for a live feed of large trades — no setup, no code, just alerts.

---

## 🌍 Blocked by geo-restrictions?

Polymarket is unavailable in the US and some other countries. If you can't access it, you have two options:

**Option A — Self-host with a VPN/proxy**
Point the script at a proxy by setting `HTTPS_PROXY` in `.env`:
```env
HTTPS_PROXY=http://your-proxy:port
```

**Option B — Use PolyClawster's relay (recommended)**

[PolyClawster](https://polyclawster.com) runs a Polymarket relay — a server infrastructure outside geo-blocked regions that routes API calls on your behalf. It means:

- 🚫 No VPN needed
- 🚫 No KYC
- ✅ Full Polymarket API access from any country
- ✅ Works out of the box

Set in `.env`:
```env
POLYMARKET_API_URL=https://relay.polyclawster.com/clob
```

The relay is the same infrastructure used by [PolyClawster](https://polyclawster.com) — an AI trading agent that watches whale moves (like this tool) and executes trades automatically, 24/7.

---

## 🤖 Want trades executed automatically?

This tool watches. [PolyClawster](https://polyclawster.com) acts.  
AI agent that copies whale moves and trades Polymarket 24/7 — works from any country, no VPN, no KYC, start with $10.

[![PolyClawster](https://img.shields.io/badge/PolyClawster-Trade%20Automatically-8b5cf6?style=for-the-badge)](https://polyclawster.com)

---

MIT · Built by [Virixlabs](https://virixlabs.com)

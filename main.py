#!/usr/bin/env python3
"""
🐋 Polymarket Whale Tracker
Monitors Polymarket for large trades and serves a web dashboard.
"""

import os
import sys
import time
import logging
import threading
import requests
import yaml
import csv
import json
import argparse
from datetime import datetime, timezone
from collections import deque
from dotenv import load_dotenv
from colorama import init, Fore, Style
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

init(autoreset=True)
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── In-memory store ──────────────────────────────────────
whale_trades: deque = deque(maxlen=100)   # last 100 whale trades
stats = {"total": 0, "yes": 0, "no": 0, "last_updated": ""}

# ── FastAPI app ──────────────────────────────────────────
app = FastAPI(title="Polymarket Whale Tracker")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>🐋 Polymarket Whale Tracker</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg: #050810;
    --surface: #0d1117;
    --border: #1a2332;
    --accent: #00d4ff;
    --yes: #00ff88;
    --no: #ff4466;
    --text: #e2e8f0;
    --muted: #64748b;
    --card: #0a0f1a;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
  }
  /* animated grid bg */
  body::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }
  .container { max-width: 1200px; margin: 0 auto; padding: 24px; position: relative; z-index: 1; }

  /* header */
  header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 32px; padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }
  .logo { display: flex; align-items: center; gap: 12px; }
  .logo-icon { font-size: 32px; animation: bob 3s ease-in-out infinite; }
  @keyframes bob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
  .logo h1 { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .logo h1 span { color: var(--accent); }
  .status {
    display: flex; align-items: center; gap: 8px;
    font-size: 11px; color: var(--muted);
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--yes);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }
  #last-updated { color: var(--muted); font-size: 11px; }

  /* stats row */
  .stats {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
    margin-bottom: 28px;
  }
  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative; overflow: hidden;
  }
  .stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  }
  .stat-card.total::before { background: var(--accent); }
  .stat-card.yes::before { background: var(--yes); }
  .stat-card.no::before { background: var(--no); }
  .stat-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
  .stat-value { font-family: 'Syne', sans-serif; font-size: 36px; font-weight: 800; }
  .stat-card.total .stat-value { color: var(--accent); }
  .stat-card.yes .stat-value { color: var(--yes); }
  .stat-card.no .stat-value { color: var(--no); }

  /* countdown */
  .refresh-bar {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 20px; font-size: 11px; color: var(--muted);
  }
  .progress-track {
    flex: 1; height: 2px; background: var(--border); border-radius: 2px; overflow: hidden;
  }
  .progress-fill {
    height: 100%; background: var(--accent);
    border-radius: 2px;
    transition: width 1s linear;
  }

  /* table */
  .table-wrap {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }
  .table-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
  }
  .table-header h2 { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; }
  .badge {
    background: rgba(0,212,255,0.1); color: var(--accent);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 20px; padding: 2px 10px; font-size: 11px;
  }
  table { width: 100%; border-collapse: collapse; }
  th {
    text-align: left; padding: 12px 20px;
    font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 2px;
    border-bottom: 1px solid var(--border);
  }
  td { padding: 14px 20px; font-size: 13px; border-bottom: 1px solid rgba(26,35,50,0.5); }
  tr:last-child td { border-bottom: none; }
  tr { transition: background 0.15s; }
  tr:hover td { background: rgba(0,212,255,0.03); }

  .side-yes {
    display: inline-flex; align-items: center; gap: 6px;
    color: var(--yes); font-weight: 700; font-size: 12px;
  }
  .side-no {
    display: inline-flex; align-items: center; gap: 6px;
    color: var(--no); font-weight: 700; font-size: 12px;
  }
  .amount { color: #fbbf24; font-weight: 700; }
  .market { color: var(--text); max-width: 340px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .price { color: var(--muted); }
  .ts { color: var(--muted); font-size: 11px; }

  .empty {
    text-align: center; padding: 60px 20px;
    color: var(--muted); font-size: 13px;
  }
  .empty .emoji { font-size: 40px; display: block; margin-bottom: 12px; }

  /* new row animation */
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  .new-row td { animation: slideIn 0.4s ease forwards; }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo">
      <span class="logo-icon">🐋</span>
      <h1>Polymarket <span>Whale</span> Tracker</h1>
    </div>
    <div class="status">
      <div class="dot"></div>
      <span>LIVE</span>
      &nbsp;·&nbsp;
      <span id="last-updated">–</span>
    </div>
  </header>

  <div class="stats">
    <div class="stat-card total">
      <div class="stat-label">Total Whales</div>
      <div class="stat-value" id="stat-total">0</div>
    </div>
    <div class="stat-card yes">
      <div class="stat-label">YES Trades</div>
      <div class="stat-value" id="stat-yes">0</div>
    </div>
    <div class="stat-card no">
      <div class="stat-label">NO Trades</div>
      <div class="stat-value" id="stat-no">0</div>
    </div>
  </div>

  <div class="refresh-bar">
    <span id="countdown">refresh in 30:00</span>
    <div class="progress-track">
      <div class="progress-fill" id="progress" style="width:100%"></div>
    </div>
  </div>

  <div class="table-wrap">
    <div class="table-header">
      <h2>Recent Whale Trades</h2>
      <span class="badge" id="count-badge">0 trades</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Market</th>
          <th>Side</th>
          <th>Amount</th>
          <th>Price</th>
        </tr>
      </thead>
      <tbody id="trades-body">
        <tr><td colspan="5" class="empty"><span class="emoji">🌊</span>Waiting for whale trades...</td></tr>
      </tbody>
    </table>
  </div>
</div>

<script>
const REFRESH_MS = 5 * 60 * 1000;  // 5 นาที
let timeLeft = REFRESH_MS / 1000;
let knownIds = new Set();

function fmt(ts) {
  if (!ts) return '–';
  const d = new Date(ts.includes('T') ? ts : ts.replace(' ', 'T') + 'Z');
  return d.toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
}

function buildRow(t, isNew) {
  const side = t.side === 'YES'
    ? `<span class="side-yes">▲ YES</span>`
    : `<span class="side-no">▼ NO</span>`;
  const cls = isNew ? 'class="new-row"' : '';
  return `<tr ${cls}>
    <td class="ts">${fmt(t.timestamp)}</td>
    <td class="market" title="${t.market}">${t.market}</td>
    <td>${side}</td>
    <td class="amount">$${Number(t.amount_usd).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})}</td>
    <td class="price">${Number(t.price).toFixed(4)}</td>
  </tr>`;
}

async function fetchData() {
  try {
    const res = await fetch('/api/trades');
    const data = await res.json();

    document.getElementById('stat-total').textContent = data.stats.total;
    document.getElementById('stat-yes').textContent = data.stats.yes;
    document.getElementById('stat-no').textContent = data.stats.no;
    document.getElementById('last-updated').textContent = 'updated ' + new Date().toLocaleTimeString();
    document.getElementById('count-badge').textContent = data.trades.length + ' trades';

    const tbody = document.getElementById('trades-body');
    if (data.trades.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty"><span class="emoji">🌊</span>Waiting for whale trades...</td></tr>';
      return;
    }

    const newIds = new Set(data.trades.map(t => t.id));
    const rows = data.trades.map(t => buildRow(t, !knownIds.has(t.id))).join('');
    tbody.innerHTML = rows;
    knownIds = newIds;
  } catch(e) {
    console.error('Fetch error:', e);
  }
}

// countdown timer
function startCountdown() {
  timeLeft = REFRESH_MS / 1000;
  const interval = setInterval(() => {
    timeLeft--;
    const m = Math.floor(timeLeft / 60).toString().padStart(2,'0');
    const s = (timeLeft % 60).toString().padStart(2,'0');
    document.getElementById('countdown').textContent = `refresh in ${m}:${s}`;
    const pct = (timeLeft / (REFRESH_MS / 1000)) * 100;
    document.getElementById('progress').style.width = pct + '%';
    if (timeLeft <= 0) {
      clearInterval(interval);
      fetchData();
      startCountdown();
    }
  }, 1000);
}

fetchData();
startCountdown();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


@app.get("/api/trades")
async def get_trades():
    return JSONResponse({
        "trades": list(whale_trades),
        "stats": stats,
    })


# ── Config ───────────────────────────────────────────────
def load_config(path="config.yaml"):
    config = {
        "min_trade_size": 500,
        "check_interval": 30,
        "telegram": {"bot_token": "", "chat_id": ""},
        "discord": {"webhook_url": ""},
        "polymarket": {"api_url": "https://data-api.polymarket.com"},
    }
    if os.path.exists(path):
        with open(path) as f:
            loaded = yaml.safe_load(f)
            if loaded:
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in config:
                        config[k].update(v)
                    else:
                        config[k] = v

    if os.getenv("MIN_TRADE_SIZE"):
        config["min_trade_size"] = float(os.getenv("MIN_TRADE_SIZE"))
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        config["telegram"]["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    if os.getenv("TELEGRAM_CHAT_ID"):
        config["telegram"]["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")
    if os.getenv("DISCORD_WEBHOOK_URL"):
        config["discord"]["webhook_url"] = os.getenv("DISCORD_WEBHOOK_URL")
    if os.getenv("CHECK_INTERVAL"):
        config["check_interval"] = int(os.getenv("CHECK_INTERVAL"))
    return config


# ── Fetch trades ─────────────────────────────────────────
def fetch_recent_trades(limit=100):
    url = "https://data-api.polymarket.com/trades"
    params = {"limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return []
    except Exception as e:
        logger.warning(f"⚠️  Error fetching trades: {e}")
        return []


def format_side(side):
    s = str(side).upper()
    if s in ("YES", "BUY", "1"): return "YES"
    if s in ("NO", "SELL", "0"): return "NO"
    return s


def parse_usd(trade):
    try:
        return float(trade.get("size", 0)) * float(trade.get("price", 0))
    except:
        return 0.0


_market_cache = {}

def get_market_title(condition_id):
    if not condition_id: return "Unknown Market"
    if condition_id in _market_cache: return _market_cache[condition_id]
    try:
        resp = requests.get("https://gamma-api.polymarket.com/markets",
                            params={"condition_id": condition_id}, timeout=8)
        data = resp.json()
        info = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
        title = info.get("question") or info.get("title") or f"Market {condition_id[:10]}..."
    except:
        title = f"Market {condition_id[:10]}..."
    _market_cache[condition_id] = title
    return title


# ── Tracker loop ─────────────────────────────────────────
def tracker_loop(config):
    min_size = float(config["min_trade_size"])
    interval = int(config.get("check_interval", 30))
    seen_ids = set()
    first_run = True

    logger.info(f"🐋 Whale Tracker started — min ${min_size:,.0f}, interval {interval}s")

    while True:
        trades = fetch_recent_trades()
        new_seen = set()

        for trade in trades:
            tid = trade.get("id") or trade.get("trade_id") or str(trade)
            new_seen.add(tid)
            if first_run or tid in seen_ids:
                continue

            amount = parse_usd(trade)
            if amount < min_size:
                continue

            side = format_side(trade.get("side") or trade.get("outcome", ""))
            price = float(trade.get("price", 0))
            condition_id = trade.get("market") or trade.get("condition_id", "")
            ts_raw = trade.get("timestamp") or trade.get("created_at", "")
            try:
                if isinstance(ts_raw, (int, float)):
                    ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    ts = str(ts_raw)[:19].replace("T", " ")
            except:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            market = (trade.get("title") or trade.get("question") or get_market_title(condition_id)).strip()

            entry = {
                "id": tid,
                "timestamp": ts,
                "market": market,
                "side": side,
                "amount_usd": round(amount, 2),
                "price": price,
            }
            whale_trades.appendleft(entry)
            stats["total"] += 1
            if side == "YES": stats["yes"] += 1
            else: stats["no"] += 1
            stats["last_updated"] = ts

            logger.info(f"🐋 WHALE: {market[:40]} | {side} | ${amount:,.2f}")

            # Send Telegram
            bot_token = config["telegram"]["bot_token"]
            chat_id = config["telegram"]["chat_id"]
            if bot_token and chat_id:
                msg = f"🐋 *WHALE ALERT*\n*Market:* {market}\n*Side:* {side}\n*Amount:* ${amount:,.2f}\n*Price:* {price:.4f}"
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={{"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}},
                        timeout=10
                    )
                except Exception as e:
                    logger.warning(f"Telegram error: {str(e)}")

        seen_ids = new_seen
        first_run = False
        time.sleep(interval)


# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
    config = load_config()

    # Start tracker in background thread
    t = threading.Thread(target=tracker_loop, args=(config,), daemon=True)
    t.start()

    # Start web server
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 Dashboard running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

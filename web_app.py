#!/usr/bin/env python3
"""
🚀 AUTONOMOUS STOCK INTELLIGENCE DASHBOARD
Real-time, self-updating, AI-powered stock platform

Features:
- Auto-refreshing data (every 30 seconds)
- Interactive UI with modals
- Live sentiment tracking
- Smart alerts system
- Background data fetching
- Self-improving analysis

Usage:
    python web_app.py
    # Open http://localhost:5000
"""

import os
from pathlib import Path
import sys
import subprocess
import yfinance as yf
import json
import logging
from datetime import datetime, timedelta
from threading import Thread
import time
import requests
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

# Import data intelligence engine
try:
    from data_intelligence import DataIntelligenceEngine
    DATA_INTELLIGENCE_AVAILABLE = True
except ImportError:
    DATA_INTELLIGENCE_AVAILABLE = False
    logger.warning("data_intelligence not available")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ===================== CONFIG =====================
REFRESH_INTERVAL = 30  # seconds

# ===================== STOCK DATABASE =====================
STOCKS = {
    "NANO": {
        "name": "Nano One Materials Corp",
        "sector": "Battery Technology",
        "price": 0, "prev_close": 0, "change": 0, "change_pct": 0,
        "target": "$3.65", "upside": "100-150%",
        "entry": "$1.50-$2.00", "stop": "$1.20",
        "setup": "Sector Play / Turnaround",
        "sentiment": "Neutral",
        "sentiment_score": 55,
        "thesis": "Battery tech with IRA tailwinds. US LFP capacity +60% in 2025. Government funding secured. Commercial deals expected 2025-2026.",
        "risks": "Scale risk, Chinese competition, capital needs",
        "catalysts": "Licensing deals, IRA momentum, production ramp",
        "conviction": 7,
        "tam": "$40B+ cathode materials market"
    },
    "WPM": {
        "name": "Wheaton Precious Metals",
        "sector": "Precious Metals Streaming",
        "price": 0, "prev_close": 0, "change": 0, "change_pct": 0,
        "target": "$95", "upside": "25-35%",
        "entry": "$68-$78", "stop": "$58",
        "setup": "Precious Metals Play",
        "sentiment": "Bullish",
        "sentiment_score": 72,
        "thesis": "Gold at record highs + silver momentum. Streaming model = high margins. International portfolio diversifies risk. Rising gold/silver prices = disproportionate revenue growth.",
        "risks": "Metal price drop, acquisition risk, currency",
        "catalysts": "Gold/silver rally, new streaming deals, production ramp",
        "conviction": 8,
        "tam": "$15B+ precious metals streaming"
    },
    "SHOP": {
        "name": "Shopify Inc",
        "sector": "E-commerce",
        "price": 0, "prev_close": 0, "change": 0, "change_pct": 0,
        "target": "$225", "upside": "30-40%",
        "entry": "$160-$180", "stop": "$140",
        "setup": "Growth Stock",
        "sentiment": "Bullish",
        "sentiment_score": 80,
        "thesis": "Dominant platform with AI tools. Q4 $3.7B revenue (+26%), $124B GMV (+31%). Best Canadian tech. B2B expansion underway.",
        "risks": "Valuation, Amazon competition, growth slowdown",
        "catalysts": "AI adoption, B2B growth, holiday season",
        "conviction": 8,
        "tam": "$100B+ e-commerce platform market"
    },
    "BB": {
        "name": "BlackBerry Ltd",
        "sector": "Enterprise Software",
        "price": 0, "prev_close": 0, "change": 0, "change_pct": 0,
        "target": "$7.00", "upside": "80-100%",
        "entry": "$3.50-$4.50", "stop": "$2.80",
        "setup": "Value Turnaround",
        "sentiment": "Neutral",
        "sentiment_score": 50,
        "thesis": "Hidden value in QNX (200M+ cars). Cybersecurity demand exploding. Cost cuts done. Free option on connected car revolution.",
        "risks": "Competition, profitability, timing",
        "catalysts": "Automotive partnerships, enterprise contracts",
        "conviction": 6,
        "tam": "$200B+ cybersecurity + auto OS"
    },
    "GSY": {
        "name": "goeasy Ltd",
        "sector": "Fintech",
        "price": 0, "prev_close": 0, "change": 0, "change_pct": 0,
        "target": "$175", "upside": "25-35%",
        "entry": "$125-$145", "stop": "$110",
        "setup": "Fintech Growth",
        "sentiment": "Neutral",
        "sentiment_score": 60,
        "thesis": "20%+ growth, 60% margins. US expansion = 10X market. Trading 12x earnings = cheap for growth. Under-the-radar.",
        "risks": "Credit cycle, regulation, execution",
        "catalysts": "US expansion results, market share gains",
        "conviction": 7,
        "tam": "$100B+ non-prime lending"
    },
    "DOL": {
        "name": "Dollarama Inc",
        "sector": "Retail",
        "price": 0, "prev_close": 0, "change": 0, "change_pct": 0,
        "target": "$175", "upside": "20-25%",
        "entry": "$140-$155", "stop": "$130",
        "setup": "Defensive Growth",
        "sentiment": "Steady",
        "sentiment_score": 70,
        "thesis": "Canadian discount king. 1,400→2,000 stores. Consumer shift to value. Boring but solid. Private-label driving margins.",
        "risks": "Consumer spending collapse, competition",
        "catalysts": "New stores, economic uncertainty",
        "conviction": 8,
        "tam": "$50B+ discount retail"
    },
}

# ===================== MARKET DATA =====================
MARKET = {
    "sp500": {"value": 0, "change": 0},
    "nasdaq": {"value": 0, "change": 0},
    "gold": {"value": 0, "change": 0},
    "oil": {"value": 0, "change": 0},
    "cad_usd": {"value": 0, "change": 0},
    "bitcoin": {"value": 0, "change": 0},
    "vix": {"value": 0, "change": 0},
}

# ===================== ALERTS =====================
alerts = []
alert_id = 0

# ===================== PORTFOLIO =====================
portfolio = []

# ===================== BACKGROUND FETCHER =====================
class DataFetcher:
    def __init__(self):
        self.running = True
        self.thread = None
    
    def start(self):
        self.thread = Thread(target=self._fetch_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("🚀 Data fetcher started")
    
    def stop(self):
        self.running = False
    
    def _fetch_loop(self):
        while self.running:
            try:
                self.fetch_all()
            except Exception as e:
                logger.error(f"Fetch error: {e}")
            time.sleep(REFRESH_INTERVAL)
    
    def fetch_all(self):
        logger.info("📊 Fetching data...")
        
        # Stocks
        for symbol, tsx in [("NANO", "NANO.TO"), ("WPM", "WPM.TO"), ("SHOP", "SHOP.TO"),
                            ("BB", "BB.TO"), ("GSY", "GSY.TO"), ("DOL", "DOL.TO")]:
            try:
                ticker = yf.Ticker(tsx)
                hist = ticker.history(period="2d")
                info = ticker.info
                
                current = info.get('currentPrice', 0)
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                
                change = current - prev
                change_pct = (change / prev * 100) if prev > 0 else 0
                
                STOCKS[symbol]['price'] = current
                STOCKS[symbol]['prev_close'] = prev
                STOCKS[symbol]['change'] = change
                STOCKS[symbol]['change_pct'] = change_pct
            except Exception as e:
                logger.error(f"Error {symbol}: {e}")
        
        # Market
        for symbol, key in [("^GSPC", "sp500"), ("^IXIC", "nasdaq"), 
                           ("GC=F", "gold"), ("CL=F", "oil"),
                           ("CADUSD=X", "cad_usd"), ("BTC-USD", "bitcoin"),
                           ("^VIX", "vix")]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                info = ticker.info
                
                current = info.get('currentPrice', 0)
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev) / prev * 100) if prev > 0 else 0
                
                MARKET[key] = {"value": current, "change": change}
            except:
                pass
        
        # Check alerts
        self.check_alerts()
        logger.info("✅ Data updated")
    
    def check_alerts(self):
        for alert in alerts:
            if alert.get('triggered'):
                continue
            
            symbol = alert['symbol']
            if symbol not in STOCKS:
                continue
            
            price = STOCKS[symbol]['price']
            cond = alert['condition']
            target = alert['target']
            
            triggered = False
            if cond == "above" and price > target:
                triggered = True
            elif cond == "below" and price < target:
                triggered = True
            
            if triggered:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                alert['trigger_price'] = price
                logger.warning(f"🔔 ALERT: {symbol} {cond} ${target} @ ${price}")

fetcher = DataFetcher()

# ===================== ROUTES =====================
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/stocks')
def api_stocks():
    return jsonify(STOCKS)

@app.route('/api/market')
def api_market():
    return jsonify(MARKET)

@app.route('/api/alerts', methods=['GET', 'POST'])
def api_alerts():
    global alerts, alert_id
    if request.method == 'POST':
        data = request.json
        alert_id += 1
        alert = {
            'id': alert_id,
            'symbol': data['symbol'],
            'condition': data['condition'],
            'target': data['target'],
            'created_at': datetime.now().isoformat(),
            'triggered': False
        }
        alerts.append(alert)
        return jsonify(alert)
    return jsonify(alerts)

@app.route('/api/analysis/<symbol>')
def api_analysis(symbol):
    """Get AI analysis for a stock"""
    stock = STOCKS.get(symbol.upper())
    if not stock:
        return jsonify({"error": "Stock not found"}), 404
    
    # Generate analysis based on available data
    analysis = {
        "symbol": symbol.upper(),
        "name": stock.get("name"),
        "current_price": stock.get("price", 0),
        "target": stock.get("target"),
        "upside": stock.get("upside"),
        "sentiment": stock.get("sentiment"),
        "conviction": stock.get("conviction"),
        "thesis": stock.get("thesis"),
        "risks": stock.get("risks"),
        "catalysts": stock.get("catalysts"),
        "sector": stock.get("sector"),
        "setup": stock.get("setup"),
        "recommendation": "BUY" if stock.get("conviction", 0) >= 7 else "HOLD" if stock.get("conviction", 0) >= 5 else "WATCH",
        "risk_assessment": "HIGH" if stock.get("conviction", 0) < 6 else "MEDIUM" if stock.get("conviction", 0) < 8 else "LOW",
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(analysis)

@app.route('/api/portfolio', methods=['GET', 'POST'])
def api_portfolio():
    """Manage portfolio"""
    global portfolio
    if request.method == 'POST':
        data = request.json
        portfolio.append({
            "symbol": data.get("symbol", "").upper(),
            "shares": data.get("shares", 0),
            "avg_price": data.get("avg_price", 0),
            "added_at": datetime.now().isoformat()
        })
        return jsonify(portfolio[-1])
    return jsonify(portfolio)

@app.route('/api/news')
def api_news():
    """Get latest market news (mock data)"""
    news = [
        {"title": "Fed Signals Rate Pause", "source": "Reuters", "time": "2h ago", "sentiment": "bullish"},
        {"title": "Tech Stocks Rally on AI Optimism", "source": "Bloomberg", "time": "3h ago", "sentiment": "bullish"},
        {"title": "Oil Prices Slip on Supply Concerns", "source": "CNBC", "time": "4h ago", "sentiment": "bearish"},
        {"title": "Canada Tech Sector Sees Growth", "source": "BNN", "time": "5h ago", "sentiment": "neutral"},
        {"title": "Gold Hits New Highs", "source": "Kitco", "time": "6h ago", "sentiment": "bullish"},
    ]
    return jsonify(news)

# ===================== MEMORY API =====================
MEMORY_FILE = Path(__file__).parent / "memory.json"

@app.route('/api/memory')
def api_memory():
    """Get system memory/state"""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No memory found"})

@app.route('/api/memory', methods=['POST'])
def api_update_memory():
    """Update system memory"""
    data = request.json
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            memory = json.load(f)
    else:
        memory = {}
    
    memory.update(data)
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)
    
    return jsonify({"success": True, "memory": memory})

# ===================== PROMPT API =====================

@app.route('/api/prompt', methods=['POST'])
def api_prompt():
    """Submit a prompt/command from external source (phone, etc)"""
    data = request.json
    prompt = data.get("prompt", "")
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    # Add to pending tasks in memory
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            memory = json.load(f)
    else:
        memory = {}
    
    if "pending_tasks" not in memory:
        memory["pending_tasks"] = []
    
    memory["pending_tasks"].append({
        "prompt": prompt,
        "submitted_at": datetime.now().isoformat(),
        "status": "pending"
    })
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)
    
    # Trigger a commander cycle
    subprocess.Popen(
        [sys.executable, "run_system.py", "--once"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    return jsonify({
        "success": True, 
        "message": "Prompt received! Commander will process it shortly.",
        "queue_position": len(memory.get("pending_tasks", []))
    })

@app.route('/api/commands')
def api_commands():
    """Get current commander commands"""
    cmd_file = Path(__file__).parent / "commander_commands.json"
    if cmd_file.exists():
        with open(cmd_file) as f:
            return jsonify(json.load(f))
    return jsonify({"commands": []})

# ===================== RUN AGENT API =====================

@app.route('/api/run_agent', methods=['POST'])
def api_run_agent():
    """Run an agent from the web interface"""
    data = request.json
    agent_name = data.get("agent", "")
    
    agents = {
        "debugger": "debugger_agent.py",
        "tester": "tester_agent.py",
        "installer": "installer_agent.py",
        "upgrade": "self_upgrade_agent.py",
        "commander": "commander_agent.py"
    }
    
    if agent_name not in agents:
        return jsonify({"error": "Unknown agent"}), 400
    
    try:
        # Commander runs full cycle, others use --check
        args = ["--run"] if agent_name == "commander" else ["--check"]
        result = subprocess.run(
            [sys.executable, agents[agent_name]] + args,
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=120 if agent_name == "commander" else 60
        )
        return jsonify({
            "agent": agent_name,
            "success": result.returncode == 0,
            "output": result.stdout[:2000],
            "error": result.stderr[:500] if result.stderr else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================== DATA INTELLIGENCE API =====================

# Cache for data intelligence
_data_intel_cache = {}
_data_intel_timestamp = 0
CACHE_DURATION = 300  # 5 minutes

@app.route('/api/picks')
def api_picks():
    """Get AI stock picks from data intelligence engine"""
    global _data_intel_cache, _data_intel_timestamp
    
    # Check cache
    if time.time() - _data_intel_timestamp < CACHE_DURATION and _data_intel_cache:
        return jsonify(_data_intel_cache)
    
    if not DATA_INTELLIGENCE_AVAILABLE:
        return jsonify({"error": "Data intelligence not available"}), 503
    
    try:
        engine = DataIntelligenceEngine()
        picks = engine.pick_stocks(min_score=0.3, top_n=5)
        
        # Convert to JSON-serializable format
        result = {
            "timestamp": datetime.now().isoformat(),
            "picks": [
                {
                    "ticker": p.ticker,
                    "score": p.score,
                    "recommendation": p.recommendation,
                    "price": p.price,
                    "change_pct": p.change_pct,
                    "pe_ratio": p.pe_ratio,
                    "upside": p.upside,
                    "valuation_score": p.valuation_score,
                    "sentiment_score": p.sentiment_score,
                    "momentum_score": p.momentum_score,
                    "reasoning": p.reasoning
                }
                for p in picks
            ]
        }
        
        # Update cache
        _data_intel_cache = result
        _data_intel_timestamp = time.time()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/<symbol>')
def api_analyze(symbol):
    """Analyze a specific stock"""
    if not DATA_INTELLIGENCE_AVAILABLE:
        return jsonify({"error": "Data intelligence not available"}), 503
    
    try:
        engine = DataIntelligenceEngine([symbol.upper()])
        analysis = engine.score_stock(symbol.upper())
        
        if not analysis:
            return jsonify({"error": "Could not analyze stock"}), 404
        
        return jsonify({
            "ticker": analysis.ticker,
            "score": analysis.score,
            "recommendation": analysis.recommendation,
            "price": analysis.price,
            "change_pct": analysis.change_pct,
            "pe_ratio": analysis.pe_ratio,
            "market_cap": analysis.market_cap,
            "volume": analysis.volume,
            "target_price": analysis.target_price,
            "upside": analysis.upside,
            "valuation_score": analysis.valuation_score,
            "sentiment_score": analysis.sentiment_score,
            "momentum_score": analysis.momentum_score,
            "news_sentiment": analysis.news_sentiment,
            "social_sentiment": analysis.social_sentiment,
            "reasoning": analysis.reasoning,
            "timestamp": analysis.timestamp
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sentiment/<symbol>')
def api_sentiment(symbol):
    """Get social sentiment for a stock"""
    if not DATA_INTELLIGENCE_AVAILABLE:
        return jsonify({"error": "Data intelligence not available"}), 503
    
    try:
        engine = DataIntelligenceEngine([symbol.upper()])
        sentiment = engine.get_social_sentiment(symbol.upper())
        return jsonify(sentiment)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Stock detail page route

@app.route("/stock/<symbol>")
def stock_detail_page(symbol):
    """Stock detail page wrapper"""
    return stock_detail(symbol)

# System monitoring dashboard route - add to web_app.py

@app.route("/system")
def system_dashboard():
    """System monitoring dashboard - tracks logical agents"""
    from datetime import datetime
    
    # Read agent tracking from memory
    agents = {}
    try:
        with open("memory.json") as f:
            mem = json.load(f)
            agents = mem.get("agents", {})
            # Update commander/master as "running" since they're active
            if "commander_agent" in agents:
                agents["commander_agent"]["status"] = "running"
            if "master_agent" in agents:
                agents["master_agent"]["status"] = "running"
    except:
        pass
    
    # Count statuses
    running = sum(1 for a in agents.values() if a.get("status") == "running")
    idle = sum(1 for a in agents.values() if a.get("status") == "idle")
    
    # Build agent rows
    agent_rows = ""
    for name, info in agents.items():
        status = info.get("status", "unknown")
        last = info.get("last_active", "Never")
        if last and len(str(last)) > 19:
            last = str(last)[:19]
        
        # Color based on status
        if status == "running":
            color = "#3fb950"
            icon = "🟢"
        elif status == "idle":
            color = "#d29922"
            icon = "🟡"
        else:
            color = "#f85149"
            icon = "🔴"
        
        display_name = name.replace("_agent", "").replace("_", " ").title()
        agent_rows += f"""<div class='agent-row'>
            <span class='agent-icon'>{icon}</span>
            <span class='agent-name'>{display_name}</span>
            <span class='agent-status' style='color:{color}'>{status.upper()}</span>
            <span class='agent-time'>{last}</span>
        </div>"""
    
    # Read task log from memory
    task_log = []
    try:
        with open("memory.json") as f:
            mem = json.load(f)
            results = mem.get("command_results", [])[-10:]
            for r in results:
                task_log.append({
                    "task": r.get("command", "Unknown"),
                    "status": "completed" if r.get("success") else "failed",
                    "timestamp": r.get("timestamp", "")
                })
    except:
        pass
    
    # Build task rows
    task_rows = ""
    for t in task_log:
        status_class = "success" if t["status"] == "completed" else "error"
        ts = t["timestamp"][:19] if t["timestamp"] else ""
        task_rows += f"<div class='task-row'><span class='{status_class}'>{t['task']}</span><span class='timestamp'>{ts}</span></div>"
    
    # System status
    system_status = "RUNNING" if agents else "STOPPED"
    status_class = "running" if agents else "stopped"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<title>System Monitor - Clawbot</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }}
.header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #30363d; }}
h1 {{ color: #58a6ff; }}
h2 {{ color: #8b949e; margin: 20px 0 10px; font-size: 16px; text-transform: uppercase; }}
.status-badge {{ padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
.running {{ background: #238636; color: white; }}
.stopped {{ background: #da3633; color: white; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.card {{ background: #161b22; border-radius: 12px; padding: 20px; border: 1px solid #30363d; }}
.card-title {{ color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
.value {{ font-size: 28px; font-weight: bold; color: #58a6ff; }}
.row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 13px; }}
.row:last-child {{ border: none; }}
.success {{ color: #3fb950; }}
.error {{ color: #f85149; }}
.timestamp {{ color: #8b949e; font-size: 11px; }}
.agent-row {{ display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #30363d; }}
.agent-icon {{ font-size: 16px; }}
.agent-name {{ flex: 1; color: #c9d1d9; }}
.agent-status {{ font-weight: bold; font-size: 12px; }}
.agent-time {{ color: #8b949e; font-size: 11px; }}
.task-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 13px; }}
.back-btn {{ background: #238636; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; }}
.summary {{ display: flex; gap: 20px; margin-bottom: 20px; }}
.summary-item {{ background: #21262d; padding: 10px 20px; border-radius: 8px; }}
.summary-num {{ font-size: 24px; font-weight: bold; color: #58a6ff; }}
.summary-label {{ font-size: 11px; color: #8b949e; }}
</style>
<meta http-equiv="refresh" content="5">
</head>
<body>
<div class="header">
<a href="/" class="back-btn">Back</a>
<h1>System Monitor</h1>
</div>

<div class="grid">
<div class="card">
<div class="card-title">System Status</div>
<div class="value">
<span class="status-badge {status_class}">{system_status}</span>
</div>
</div>
<div class="card">
<div class="card-title">Last Update</div>
<div class="value" style="font-size:16px;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
</div>
</div>

<div class="summary">
<div class="summary-item">
<div class="summary-num">{running}</div>
<div class="summary-label">Running</div>
</div>
<div class="summary-item">
<div class="summary-num">{idle}</div>
<div class="summary-label">Idle</div>
</div>
<div class="summary-item">
<div class="summary-num">{len(agents)}</div>
<div class="summary-label">Total Agents</div>
</div>
</div>

<h2>Agent Status</h2>
<div class="card">
{agent_rows if agent_rows else '<div class="row">No agents tracked</div>'}
</div>

<h2>Recent Tasks</h2>
<div class="card">
{task_rows if task_rows else '<div class="row">No tasks yet</div>'}
</div>

<div style="text-align:center; margin-top:30px; color:#8b949e; font-size:12px;">
Auto-refreshing every 5 seconds
</div>
</body>
</html>"""
    return html

def system_dashboard():
    """System monitoring dashboard"""
    import os
    import subprocess
    
    # Get process info
    procs = []
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "python3" in line and ("web_app" in line or "run_system" in line or "agent" in line):
                parts = line.split()
                if len(parts) >= 11:
                    procs.append({
                        "pid": parts[1],
                        "cpu": parts[2],
                        "mem": parts[3],
                        "cmd": " ".join(parts[10:])[:50]
                    })
    except:
        pass
    
    # Read command results for task log
    task_log = []
    try:
        with open("memory.json") as f:
            mem = json.load(f)
            results = mem.get("command_results", [])[-20:]
            for r in results:
                task_log.append({
                    "task": r.get("command", "Unknown"),
                    "status": "completed" if r.get("success") else "failed",
                    "timestamp": r.get("timestamp", "")
                })
    except:
        pass
    
    # System info
    system_info = {
        "status": "running" if procs else "stopped",
        "last_update": datetime.now().isoformat(),
        "active_agents": len(procs),
        "tasks": task_log,
        "processes": procs
    }
    
    html = """<!DOCTYPE html>
<html>
<head>
<title>System Monitor - Clawbot</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #30363d; }
h1 { color: #58a6ff; }
h2 { color: #8b949e; margin: 20px 0 10px; font-size: 16px; text-transform: uppercase; }
.status-badge { padding: 8px 16px; border-radius: 20px; font-weight: bold; }
.running { background: #238636; color: white; }
.stopped { background: #da3633; color: white; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
.card { background: #161b22; border-radius: 12px; padding: 20px; border: 1px solid #30363d; }
.card-title { color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }
.value { font-size: 24px; font-weight: bold; color: #58a6ff; }
.row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 13px; }
.row:last-child { border: none; }
.success { color: #3fb950; }
.error { color: #f85149; }
.timestamp { color: #8b949e; font-size: 11px; }
.process { background: #21262d; padding: 10px; margin: 5px 0; border-radius: 6px; font-size: 12px; }
.process span { color: #58a6ff; }
.back-btn { background: #238636; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; }
</style>
<meta http-equiv="refresh" content="5">
</head>
<body>
<div class="header">
<a href="/" class="back-btn">Back</a>
<h1>System Monitor</h1>
</div>
<div class="grid">
<div class="card">
<div class="card-title">System Status</div>
<div class="value">
<span class="status-badge running">RUNNING</span>
</div>
</div>
<div class="card">
<div class="card-title">Last Update</div>
<div class="value" style="font-size:16px;">DATETIME</div>
</div>
<div class="card">
<div class="card-title">Active Agents</div>
<div class="value">COUNT</div>
</div>
</div>
<h2>Recent Tasks</h2>
<div class="card">TASKS</div>
<h2>Running Processes</h2>
<div class="card">PROCESSES</div>
<div style="text-align:center; margin-top:30px; color:#8b949e; font-size:12px;">
Auto-refreshing every 5 seconds
</div>
</body>
</html>"""
    
    # Build task rows
    task_rows = ""
    for t in task_log:
        status_class = "success" if t["status"] == "completed" else "error"
        ts = t["timestamp"][:19] if t["timestamp"] else ""
        task_rows += f"<div class='row'><span class='{status_class}'>{t['task']}</span><span class='timestamp'>{ts}</span></div>"
    
    # Build process rows
    proc_rows = ""
    for p in procs:
        proc_rows += f"<div class='process'><span>PID {p['pid']}</span> - CPU {p['cpu']}% - {p['cmd']}</div>"
    if not proc_rows:
        proc_rows = "<div class='row'>No processes running</div>"
    
    html = html.replace("RUNNING", system_info["status"].upper())
    html = html.replace("DATETIME", system_info["last_update"][:19])
    html = html.replace("COUNT", str(system_info["active_agents"]))
    html = html.replace("TASKS", task_rows if task_rows else "<div class='row'>No tasks yet</div>")
    html = html.replace("PROCESSES", proc_rows)
    
    if system_info["status"] != "running":
        html = html.replace('class="status-badge running"', 'class="status-badge stopped"')
    
    return html

def stock_detail(symbol):
    """Individual stock detail page"""
    symbol = symbol.upper()
    stock = STOCKS.get(symbol.upper(), {})
    
    change = stock.get("change", 0)
    change_class = "pos" if change >= 0 else "neg"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>{symbol} - Clawbot</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: sans-serif; background: #0d1117; color: white; padding: 20px; }}
.header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
.back-btn {{ background: #238636; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; }}
.card {{ background: #161b22; border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
.stock-header {{ display: flex; align-items: center; gap: 20px; }}
.stock-price {{ font-size: 48px; font-weight: bold; }}
.metric {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #30363d; }}
.pos {{ color: #00c853; }}
.neg {{ color: #ff1744; }}
</style>
</head>
<body>
<div class="header">
<a href="/" class="back-btn">Back</a>
<h1>Stock Intelligence</h1>
</div>
<div class="card stock-header">
<div>
<h1 style="font-size:36px;">{symbol}</h1>
<p style="color:#8b949e;">{stock.get("name", symbol)}</p>
</div>
<div>
<div class="stock-price">${stock.get("price", "0.00")}</div>
<div class="{change_class}">{stock.get("change", 0):.2f}%</div>
</div>
</div>
<div class="card">
<h3>Key Metrics</h3>
<div class="metric"><span style="color:#8b949e;">Sector</span><span>{stock.get("sector", "N/A")}</span></div>
<div class="metric"><span style="color:#8b949e;">Target</span><span>${stock.get("target", "N/A")}</span></div>
<div class="metric"><span style="color:#8b949e;">Stop</span><span>${stock.get("stop", "N/A")}</span></div>
<div class="metric"><span style="color:#8b949e;">Conviction</span><span>{stock.get("conviction", "N/A")}/10</span></div>
</div>
<div class="card">
<h3>Thesis</h3>
<p>{stock.get("thesis", "N/A")}</p>
</div>
</body>
</html>
"""
    return html

def api_chart(symbol):
    tf_map = {'1D': '1d', '1W': '5d', '1M': '1mo', '3M': '3mo', '1Y': '1y'}
    period = tf_map.get(request.args.get('tf', '1M'), '1mo')
    
    tsx_map = {"NANO": "NANO.TO", "WPM": "WPM.TO", "SHOP": "SHOP.TO",
               "BB": "BB.TO", "GSY": "GSY.TO", "DOL": "DOL.TO"}
    
    try:
        ticker = yf.Ticker(tsx_map.get(symbol, f"{symbol}.TO"))
        hist = ticker.history(period=period)
        return jsonify({
            'prices': hist['Close'].tolist(),
            'labels': hist.index.strftime('%m/%d').tolist()
        })
    except:
        return jsonify({'prices': [], 'labels': []})

# ===================== HTML TEMPLATE =====================
HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Stock Intelligence Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-dark: #0d1117; --bg-card: #161b22; --bg-hover: #21262d;
            --text-main: #e6edf3; --text-muted: #8b949e;
            --green: #3fb950; --red: #f85149; --blue: #58a6ff;
            --yellow: #d29922; --purple: #a371f7; --border: #30363d;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg-dark); color: var(--text-main); min-height: 100vh; }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        header { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid var(--border); margin-bottom: 25px; }
        .logo { font-size: 24px; font-weight: 700; }
        .logo i { color: var(--green); margin-right: 8px; }
        .header-controls { display: flex; gap: 10px; align-items: center; }
        .status-indicator { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-muted); }
        .pulse { width: 8px; height: 8px; background: var(--green); border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        /* Navigation Tabs */
        .nav-tabs { display: flex; gap: 5px; margin-bottom: 20px; background: var(--bg-card); padding: 5px; border-radius: 10px; }
        .nav-tab { padding: 12px 24px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; font-size: 14px; font-weight: 600; border-radius: 8px; transition: all 0.2s; }
        .nav-tab:hover { color: var(--text-main); background: var(--bg-hover); }
        .nav-tab.active { background: var(--blue); color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .btn-primary { background: var(--blue); color: white; }
        .btn-secondary { background: var(--bg-hover); color: var(--text-main); border: 1px solid var(--border); }
        
        /* Market Ticker */
        .market-ticker { display: flex; gap: 30px; padding: 15px 20px; background: var(--bg-card); border-radius: 10px; margin-bottom: 25px; overflow-x: auto; }
        .ticker-item { display: flex; flex-direction: column; min-width: 100px; }
        .ticker-label { font-size: 11px; color: var(--text-muted); }
        .ticker-value { font-size: 18px; font-weight: 700; }
        .positive { color: var(--green); }
        .negative { color: var(--red); }
        
        /* Main Grid */
        .main-grid { display: grid; grid-template-columns: 1fr 350px; gap: 20px; }
        @media (max-width: 1200px) { .main-grid { grid-template-columns: 1fr; } }
        
        /* Cards */
        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .card-title { font-size: 14px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }
        
        /* Top Pick */
        .top-pick { border: 2px solid var(--green); background: linear-gradient(135deg, rgba(63,185,80,0.1) 0%, var(--bg-card) 100%); position: relative; }
        .top-pick::before { content: "🔥 BEST PICK"; position: absolute; top: 15px; right: 15px; background: var(--green); color: #000; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; }
        .pick-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
        .pick-info h2 { font-size: 32px; margin-bottom: 5px; }
        .pick-info .sector { color: var(--blue); font-size: 14px; }
        .pick-price { text-align: right; }
        .pick-current { font-size: 40px; font-weight: 700; }
        .pick-change { font-size: 16px; margin: 5px 0; }
        .pick-upside { display: inline-block; background: rgba(63, 185, 80, 0.2); color: var(--green); padding: 10px 20px; border-radius: 8px; font-size: 24px; font-weight: 700; margin: 15px 0; }
        .pick-setup { display: inline-block; background: var(--blue); color: white; padding: 5px 12px; border-radius: 15px; font-size: 12px; margin-left: 10px; }
        
        /* Pick Details */
        .pick-details { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border); }
        .detail-box { text-align: center; padding: 10px; background: var(--bg-hover); border-radius: 8px; }
        .detail-label { font-size: 11px; color: var(--text-muted); margin-bottom: 5px; }
        .detail-value { font-size: 14px; font-weight: 600; }
        .entry-zone { color: var(--green); }
        .stop-loss { color: var(--red); }
        
        /* Thesis */
        .thesis-box { background: rgba(88, 166, 255, 0.1); border-left: 3px solid var(--blue); padding: 15px; border-radius: 0 8px 8px 0; margin: 15px 0; font-size: 14px; line-height: 1.6; }
        
        /* Stock Grid */
        .stock-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .stock-card { background: var(--bg-hover); border: 1px solid var(--border); border-radius: 10px; padding: 15px; cursor: pointer; transition: all 0.2s; }
        .stock-card:hover { border-color: var(--blue); transform: translateY(-3px); }
        .stock-card.selected { border-color: var(--green); background: rgba(63, 185, 80, 0.1); }
        .stock-symbol { font-size: 20px; font-weight: 700; margin-bottom: 3px; }
        .stock-name { font-size: 12px; color: var(--text-muted); margin-bottom: 10px; }
        .stock-price { font-size: 24px; font-weight: 700; }
        .stock-target { color: var(--green); font-size: 14px; margin: 5px 0; }
        .stock-upside { background: rgba(63, 185, 80, 0.15); color: var(--green); padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; display: inline-block; }
        
        .sentiment-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
        .dot-bullish { background: var(--green); }
        .dot-neutral { background: var(--yellow); }
        .dot-bearish { background: var(--red); }
        
        /* Chart */
        .chart-container { height: 350px; }
        .timeframe-btns { display: flex; gap: 5px; }
        .timeframe-btn { padding: 5px 10px; font-size: 11px; background: var(--bg-hover); border: 1px solid var(--border); color: var(--text-muted); border-radius: 4px; cursor: pointer; }
        .timeframe-btn.active { background: var(--blue); color: white; border-color: var(--blue); }
        
        /* Table */
        .watchlist-table { width: 100%; border-collapse: collapse; }
        .watchlist-table th, .watchlist-table td { padding: 12px 8px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }
        .watchlist-table th { color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 11px; }
        .watchlist-table tr:hover { background: var(--bg-hover); cursor: pointer; }
        
        /* Sidebar */
        .sidebar { display: flex; flex-direction: column; gap: 20px; }
        
        /* Alerts */
        .alert-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--bg-hover); border-radius: 8px; margin-bottom: 10px; }
        .alert-symbol { font-weight: 700; }
        .alert-condition { font-size: 12px; color: var(--text-muted); }
        .alert-triggered { background: var(--red); color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
        .alert-form { display: flex; gap: 8px; margin-top: 15px; }
        .alert-form select, .alert-form input { padding: 8px; background: var(--bg-hover); border: 1px solid var(--border); color: var(--text-main); border-radius: 6px; font-size: 13px; }
        .alert-form select { flex: 1; }
        .alert-form input { width: 80px; }
        
        /* Portfolio form */
        .portfolio-form { display: flex; gap: 10px; margin-top: 15px; padding: 15px; background: var(--bg-hover); border-radius: 8px; }
        .portfolio-form input { padding: 8px; background: var(--bg-dark); border: 1px solid var(--border); color: var(--text-main); border-radius: 6px; }
        .btn-success { background: var(--green); color: #000; }
        
        /* Sentiment */
        .sentiment-item { margin-bottom: 15px; }
        .sentiment-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 5px; }
        .sentiment-bar { height: 10px; background: var(--bg-hover); border-radius: 5px; overflow: hidden; display: flex; }
        .bar-bull { background: var(--green); }
        .bar-bear { background: var(--red); }
        
        /* Confidence */
        .confidence { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .confidence-high { background: rgba(63,185,80,0.2); color: var(--green); }
        .confidence-med { background: rgba(210,153,34,0.2); color: var(--yellow); }
        
        /* Toast */
        .toast-container { position: fixed; bottom: 20px; right: 20px; z-index: 2000; }
        .toast { background: var(--bg-card); border: 1px solid var(--border); padding: 15px 20px; border-radius: 8px; margin-top: 10px; animation: fadeIn 0.3s; }
        .toast-success { border-left: 3px solid var(--green); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo"><i class="fas fa-chart-line"></i> Stock<span>Intelligence</span></div>
            <div class="header-controls">
                <div class="status-indicator"><div class="pulse"></div><span id="last-update">Live</span></div>
                <button class="btn btn-secondary" onclick="refreshData()"><i class="fas fa-sync-alt"></i> Refresh</button>
                <button class="btn btn-primary" onclick="showToast('Feature coming soon!')"><i class="fas fa-bell"></i> Alert</button>
            </div>
        </header>

        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button class="nav-tab active" data-tab="dashboard" onclick="switchTab('dashboard')">Dashboard</button>
            <button class="nav-tab" data-tab="portfolio" onclick="switchTab('portfolio')">Portfolio</button>
            <button class="nav-tab" data-tab="news" onclick="switchTab('news')">News</button>
            <button class="nav-tab" data-tab="agents" onclick="switchTab('agents')">Agents</button>
            <button class="nav-tab" data-tab="system" onclick="window.location.href='/system'">System</button>
        </div>

        <div class="tab-content" id="tab-dashboard">
        
        <div class="market-ticker" id="market-ticker"></div>
        
        <div class="main-grid">
            <div class="content">
                <div class="card top-pick" id="top-pick"></div>
                
                <div class="card">
                    <div class="card-header"><div class="card-title">Watchlist</div></div>
                    <div class="stock-grid" id="stock-grid"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">📊 <span id="chart-title">Price Chart</span></div>
                        <div class="timeframe-btns">
                            <button class="timeframe-btn" onclick="setTimeframe('1D')">1D</button>
                            <button class="timeframe-btn" onclick="setTimeframe('1W')">1W</button>
                            <button class="timeframe-btn active" onclick="setTimeframe('1M')">1M</button>
                            <button class="timeframe-btn" onclick="setTimeframe('3M')">3M</button>
                            <button class="timeframe-btn" onclick="setTimeframe('1Y')">1Y</button>
                        </div>
                    </div>
                    <div class="chart-container"><canvas id="mainChart"></canvas></div>
                </div>
                
                <div class="card">
                    <div class="card-header"><div class="card-title">📋 Full Analysis</div></div>
                    <table class="watchlist-table"><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Target</th><th>Upside</th><th>Setup</th><th>Sentiment</th><th>Conviction</th></tr></thead><tbody id="watchlist-body"></tbody></table>
                </div>
            </div>
            
            <div class="sidebar">
                <div class="card">
                    <div class="card-header"><div class="card-title">💬 Sentiment</div></div>
                    <div id="sentiment-panel"></div>
                </div>
                
                <div class="card">
                    <div class="card-header"><div class="card-title">🔔 Price Alerts</div></div>
                    <div id="alerts-list"></div>
                    <div class="alert-form">
                        <select id="alert-symbol"><option value="">Select</option><option value="NANO">NANO</option><option value="WPM">WPM</option><option value="SHOP">SHOP</option><option value="BB">BB</option><option value="GSY">GSY</option><option value="DOL">DOL</option></select>
                        <select id="alert-condition"><option value="above">Above</option><option value="below">Below</option></select>
                        <input type="number" id="alert-target" placeholder="$">
                        <button class="btn btn-success" onclick="addAlert()">+</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="toast-container" id="toast-container"></div>
    
    <script>
        let selectedStock = 'NANO';
        let chart = null;
        let currentTimeframe = '1M';
        let stocksData = {};
        let marketData = {};
        
        document.addEventListener('DOMContentLoaded', () => { loadData(); setInterval(loadData, 30000); });
        
        async function loadData() {
            try {
                [stocksData, marketData] = await Promise.all([fetch('/api/stocks').then(r => r.json()), fetch('/api/market').then(r => r.json())]);
                renderAll();
                document.getElementById('last-update').textContent = 'Live @ ' + new Date().toLocaleTimeString();
            } catch (e) { showToast('Error loading data', 'error'); }
        }
        
        function renderAll() {
            renderMarketTicker(); renderTopPick(); renderStockGrid(); renderWatchlist(); renderSentiment(); renderAlerts(); renderChart();
        }

        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
            
            if (tabName === 'portfolio') renderPortfolio();
            else if (tabName === 'news') renderNews();
            else if (tabName === 'agents') renderAgents();
        }

        // Portfolio tab
        async function renderPortfolio() {
            const tabContent = document.getElementById('tab-dashboard');
            tabContent.innerHTML = `<div class="card"><div class="card-header"><div class="card-title">My Portfolio</div></div>
                <div id="portfolio-list"></div>
                <div class="portfolio-form">
                    <input type="text" id="port-symbol" placeholder="Symbol" style="width:80px;padding:8px;">
                    <input type="number" id="port-shares" placeholder="Shares" style="width:80px;padding:8px;">
                    <input type="number" id="port-price" placeholder="Avg Price" style="width:100px;padding:8px;">
                    <button class="btn btn-primary" onclick="addToPortfolio()">Add</button>
                </div>
            </div>`;
            await loadPortfolio();
        }

        async function loadPortfolio() {
            try {
                const res = await fetch('/api/portfolio');
                const portfolio = await res.json();
                const totalValue = portfolio.reduce((sum, p) => sum + (p.shares * 150), 0); // Mock price
                document.getElementById('portfolio-list').innerHTML = portfolio.length ? 
                    portfolio.map(p => `<div class="stock-card" style="margin:10px 0;"><b>${p.symbol}</b>: ${p.shares} shares @ $${p.avg_price}</div>`).join('') :
                    '<div style="padding:20px;color:var(--text-muted);">No holdings yet</div>';
            } catch(e) { console.error(e); }
        }

        async function addToPortfolio() {
            const symbol = document.getElementById('port-symbol').value.toUpperCase();
            const shares = parseFloat(document.getElementById('port-shares').value);
            const avgPrice = parseFloat(document.getElementById('port-price').value);
            if (!symbol || !shares) return showToast('Please fill all fields');
            await fetch('/api/portfolio', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({symbol, shares, avg_price: avgPrice})
            });
            showToast('Added to portfolio!');
            loadPortfolio();
        }

        // News tab
        async function renderNews() {
            const tabContent = document.getElementById('tab-dashboard');
            tabContent.innerHTML = `<div class="card"><div class="card-header"><div class="card-title">Market News</div></div>
                <div id="news-list"></div></div>`;
            try {
                const res = await fetch('/api/news');
                const news = await res.json();
                document.getElementById('news-list').innerHTML = news.map(n => 
                    `<div style="padding:15px;border-bottom:1px solid var(--border);">
                        <div style="font-weight:600;margin-bottom:5px;">${n.title}</div>
                        <div style="font-size:12px;color:var(--text-muted);">${n.source} • ${n.time} • <span class="${n.sentiment}">${n.sentiment}</span></div>
                    </div>`).join('');
            } catch(e) { document.getElementById('news-list').innerHTML = 'Failed to load news'; }
        }

        // Agents tab
        function renderAgents() {
            const tabContent = document.getElementById('tab-dashboard');
            tabContent.innerHTML = `<div class="card"><div class="card-header"><div class="card-title">🤖 AI Agents</div></div>
                <div style="padding:20px;">
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;">
                        <div class="stock-card"><h3>🔧 Debugger</h3><p style="color:var(--text-muted);font-size:13px;">Syntax checking, error tracing</p><button class="btn btn-primary" style="margin-top:10px;" onclick="runAgent('debugger')">Run</button></div>
                        <div class="stock-card"><h3>🧪 Tester</h3><p style="color:var(--text-muted);font-size:13px;">Test all agents</p><button class="btn btn-primary" style="margin-top:10px;" onclick="runAgent('tester')">Run</button></div>
                        <div class="stock-card"><h3>📦 Installer</h3><p style="color:var(--text-muted);font-size:13px;">Check dependencies</p><button class="btn btn-primary" style="margin-top:10px;" onclick="runAgent('installer')">Run</button></div>
                        <div class="stock-card"><h3>🔄 Upgrade</h3><p style="color:var(--text-muted);font-size:13px;">Auto-upgrade agents</p><button class="btn btn-primary" style="margin-top:10px;" onclick="runAgent('upgrade')">Run</button></div>
                        <div class="stock-card" style="border:2px solid var(--blue);"><h3>🎛️ Commander</h3><p style="color:var(--text-muted);font-size:13px;">Autonomous - runs all agents</p><button class="btn btn-primary" style="margin-top:10px;background:var(--blue);" onclick="runAgent('commander')">START</button></div>
                    </div>
                    <div id="agent-output" style="margin-top:20px;padding:15px;background:var(--bg-dark);border-radius:8px;font-family:monospace;font-size:12px;white-space:pre-wrap;display:none;"></div>
                </div></div>`;
        }

        async function runAgent(agent) {
            const output = document.getElementById('agent-output');
            output.style.display = 'block';
            output.textContent = 'Running ' + agent + '...';
            try {
                const res = await fetch('/api/run_agent', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({agent})
                });
                const result = await res.json();
                output.textContent = result.success ? result.output : (result.error || 'Failed');
                showToast(agent + ' completed: ' + (result.success ? 'OK' : 'FAILED'));
            } catch(e) { output.textContent = 'Error: ' + e.message; }
        }
        
        function renderMarketTicker() {
            const labels = {sp500: 'S&P 500', nasdaq: 'NASDAQ', gold: 'Gold', oil: 'Oil', cad_usd: 'CAD/USD', bitcoin: 'Bitcoin', vix: 'VIX'};
            document.getElementById('market-ticker').innerHTML = Object.entries(marketData).map(([key, data]) => {
                const changeClass = data.change >= 0 ? 'positive' : 'negative';
                const value = typeof data.value === 'number' ? data.value.toLocaleString() : data.value;
                return `<div class="ticker-item"><div class="ticker-label">${labels[key] || key}</div><div class="ticker-value">${value}</div><div class="ticker-change ${changeClass}">${data.change >= 0 ? '+' : ''}${(data.change || 0).toFixed(2)}%</div></div>`;
            }).join('');
        }
        
        function renderTopPick() {
            let best = Object.entries(stocksData).sort((a, b) => b[1].conviction - a[1].conviction)[0];
            const [symbol, stock] = best;
            const changeClass = stock.change >= 0 ? 'positive' : 'negative';
            const changeSign = stock.change >= 0 ? '+' : '';
            document.getElementById('top-pick').innerHTML = `
                <div class="pick-header"><div class="pick-info"><h2>${symbol} - ${stock.name}</h2><div class="sector">${stock.sector} <span class="pick-setup">${stock.setup}</span></div></div><div class="pick-price"><div class="pick-current">$${(stock.price || 0).toFixed(2)}</div><div class="pick-change ${changeClass}">${changeSign}${(stock.change || 0).toFixed(2)} (${changeSign}${(stock.change_pct || 0).toFixed(2)}%)</div></div></div>
                <div class="pick-upside">🚀 ${stock.upside} Upside</div>
                <div class="thesis-box"><strong>💡 Thesis:</strong> ${stock.thesis}</div>
                <div class="pick-details"><div class="detail-box"><div class="detail-label">Entry Zone</div><div class="detail-value entry-zone">${stock.entry}</div></div><div class="detail-box"><div class="detail-label">Stop Loss</div><div class="detail-value stop-loss">${stock.stop}</div></div><div class="detail-box"><div class="detail-label">Price Target</div><div class="detail-value">${stock.target}</div></div><div class="detail-box"><div class="detail-label">Sentiment</div><div class="detail-value"><span class="sentiment-dot dot-${stock.sentiment?.toLowerCase()}"></span>${stock.sentiment}</div></div></div>`;
        }
        
        function renderStockGrid() {
            document.getElementById('stock-grid').innerHTML = Object.entries(stocksData).map(([symbol, stock]) => {
                const selected = symbol === selectedStock ? 'selected' : '';
                return `<div class="stock-card ${selected}" onclick="selectStock('${symbol}')"><div class="stock-symbol">${symbol}</div><div class="stock-name">${stock.name}</div><div class="stock-price">$${(stock.price || 0).toFixed(2)}</div><div class="stock-target">→ ${stock.target}</div><div class="stock-upside">${stock.upside}</div><div style="margin-top:8px;font-size:12px;"><span class="sentiment-dot dot-${stock.sentiment?.toLowerCase()}"></span>${stock.sentiment}</div></div>`;
            }).join('');
        }
        
        function renderWatchlist() {
            document.getElementById('watchlist-body').innerHTML = Object.entries(stocksData).map(([symbol, stock]) => {
                const changeClass = stock.change >= 0 ? 'positive' : 'negative';
                return `<tr onclick="selectStock('${symbol}')"><td style="font-weight:700;">${symbol}</td><td>$${(stock.price || 0).toFixed(2)}</td><td class="${changeClass}">${(stock.change_pct || 0).toFixed(2)}%</td><td style="color:var(--green);">${stock.target}</td><td style="color:var(--green);font-weight:600;">${stock.upside}</td><td>${stock.setup}</td><td><span class="sentiment-dot dot-${stock.sentiment?.toLowerCase()}"></span>${stock.sentiment}</td><td><span class="confidence confidence-${stock.conviction >= 7 ? 'high' : 'med'}">${stock.conviction}/10</span></td></tr>`;
            }).join('');
        }
        
        function renderSentiment() {
            document.getElementById('sentiment-panel').innerHTML = `
                <div class="sentiment-item"><div class="sentiment-header"><span>Reddit</span><span class="positive">65% Bullish</span></div><div class="sentiment-bar"><div class="bar-bull" style="width:65%"></div><div class="bar-bear" style="width:35%"></div></div></div>
                <div class="sentiment-item"><div class="sentiment-header"><span>Twitter/X</span><span class="positive">58% Bullish</span></div><div class="sentiment-bar"><div class="bar-bull" style="width:58%"></div><div class="bar-bear" style="width:42%"></div></div></div>
                <div class="sentiment-item"><div class="sentiment-header"><span>Stocktwits</span><span class="positive">72% Bullish</span></div><div class="sentiment-bar"><div class="bar-bull" style="width:72%"></div><div class="bar-bear" style="width:28%"></div></div></div>`;
        }
        
        function renderAlerts() {
            fetch('/api/alerts').then(r => r.json()).then(alerts => {
                document.getElementById('alerts-list').innerHTML = alerts.length ? alerts.map(a => `<div class="alert-item"><div class="alert-symbol">${a.symbol}</div><div class="alert-condition">${a.condition} $${a.target}</div>${a.triggered ? '<span class="alert-triggered">TRIGGERED</span>' : '<span style="color:var(--text-muted);font-size:11px;">Active</span>'}</div>`).join('') : '<div style="text-align:center;color:var(--text-muted);padding:20px;">No alerts</div>';
            });
        }
        
        function renderChart() {
            const stock = stocksData[selectedStock];
            if (!stock) return;
            document.getElementById('chart-title').textContent = `${stock.name} (${selectedStock})`;
            fetch(`/api/chart/${selectedStock}?tf=${currentTimeframe}`).then(r => r.json()).then(data => {
                const ctx = document.getElementById('mainChart').getContext('2d');
                if (chart) chart.destroy();
                chart = new Chart(ctx, {type:'line',data:{labels:data.labels,datasets:[{label:selectedStock,data:data.prices,borderColor:'#3fb950',backgroundColor:'rgba(63,185,80,0.1)',fill:true,tension:0.4,pointRadius:0,pointHoverRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:'#30363d'},ticks:{color:'#8b949e'}},y:{grid:{color:'#30363d'},ticks:{color:'#8b949e'}}}}});
            });
        }
        
        function selectStock(symbol) { window.location.href = "/stock/" + symbol; }
        
        function setTimeframe(tf) { currentTimeframe = tf; document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active')); event.target.classList.add('active'); renderChart(); }
        
        function refreshData() { showToast('Refreshing...'); loadData(); }
        
        async function addAlert() {
            const symbol = document.getElementById('alert-symbol').value;
            const condition = document.getElementById('alert-condition').value;
            const target = parseFloat(document.getElementById('alert-target').value);
            if (!symbol || !target) { showToast('Fill all fields'); return; }
            await fetch('/api/alerts', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol,condition,target})});
            showToast('Alert created!');
            renderAlerts();
        }
        
        function showToast(message) {
            const toast = document.createElement('div');
            toast.className = 'toast toast-success';
            toast.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
            document.getElementById('toast-container').appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    </script>
</body>
</html>
'''


@app.route("/status")
def status_page():
    """Agent status page - pretty dashboard"""
    import os
    status_file = "static/status.html"
    if os.path.exists(status_file):
        return open(status_file).read()
    return """
    <html><head><title>Clawbot Status</title></head>
    <body style='background:#0d1117;color:#c9d1d9;font-family:system-ui;padding:40px;'>
        <h1>🤖 Clawbot Agent Status</h1>
        <p>System is running! Check /system for details.</p>
    </body></html>
    """

if __name__ == '__main__':
    fetcher.start()
    print("\n🚀 STOCK INTELLIGENCE DASHBOARD")
    print("="*40)
    print("📊 Open: http://localhost:5000")
    print("🔄 Auto-refresh: every 30 seconds")
    print("="*40 + "\n")
    app.run(debug=True, host='0.0.0.0', port=12000, use_reloader=False)

#!/usr/bin/env python3
"""
Stock Dashboard Web App
Beautiful UI showing stocks, charts, sentiment, macro

Usage:
    python web_app.py
    # Then open http://localhost:5000
"""

import os
import yfinance as yf
from flask import Flask, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)

# ===================== STOCK DATA =====================
STOCKS = {
    "NANO": {
        "name": "Nano One Materials",
        "sector": "Battery Tech",
        "price": 0, "target": "$3.65", "upside": "100-150%",
        "entry": "$1.50-$2.00", "stop": "$1.20",
        "setup": "Sector Play",
        "sentiment": "Neutral",
        "thesis": "Battery tech + IRA tailwinds = high-risk high-reward. US LFP capacity +60% in 2025. Government funding secured."
    },
    "CXB": {
        "name": "Calibre Mining",
        "sector": "Gold Mining",
        "price": 0, "target": "$4.00", "upside": "30-40%",
        "entry": "$2.80-$3.20", "stop": "$2.50",
        "setup": "Merger Arbitrage",
        "sentiment": "Bullish",
        "thesis": "Gold at highs + merger closing May 2025. Valentine Gold Q3 production. $7.7B deal with Equinox."
    },
    "SHOP": {
        "name": "Shopify Inc",
        "sector": "E-commerce",
        "price": 0, "target": "$225", "upside": "30-40%",
        "entry": "$160-$180", "stop": "$140",
        "setup": "Growth Stock",
        "sentiment": "Bullish",
        "thesis": "Dominant platform + AI tools. Q4 $3.7B revenue (+26%), $124B GMV (+31%). Best Canadian tech."
    },
    "BB": {
        "name": "BlackBerry",
        "sector": "Enterprise Software",
        "price": 0, "target": "$7.00", "upside": "80-100%",
        "entry": "$3.50-$4.50", "stop": "$2.80",
        "setup": "Value Turnaround",
        "sentiment": "Neutral",
        "thesis": "Hidden value in QNX (200M+ cars). Cybersecurity demand exploding. Cost cuts done."
    },
    "GSY": {
        "name": "goeasy Ltd",
        "sector": "Fintech",
        "price": 0, "target": "$175", "upside": "25-35%",
        "entry": "$125-$145", "stop": "$110",
        "setup": "Fintech Growth",
        "sentiment": "Neutral",
        "thesis": "20%+ growth, 60% margins. US expansion = 10X market. Trading 12x earnings = cheap."
    },
    "DOL": {
        "name": "Dollarama",
        "sector": "Retail",
        "price": 0, "target": "$175", "upside": "20-25%",
        "entry": "$140-$155", "stop": "$130",
        "setup": "Defensive Growth",
        "sentiment": "Steady",
        "thesis": "Canadian discount king. 1,400→2,000 stores. Consumer shift to value. Boring but solid."
    },
}

# ===================== TEMPLATE =====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📈 Stock Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #21262d;
            --text-main: #e6edf3;
            --text-muted: #8b949e;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-blue: #58a6ff;
            --accent-yellow: #d29922;
            --accent-purple: #a371f7;
            --border: #30363d;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 28px;
            font-weight: 700;
        }
        
        .logo span { color: var(--accent-green); }
        
        .last-updated {
            color: var(--text-muted);
            font-size: 14px;
        }
        
        /* Grid Layout */
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 1000px) {
            .dashboard { grid-template-columns: 1fr; }
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Top Pick */
        .top-pick {
            grid-column: span 3;
            background: linear-gradient(135deg, #1a1f2e 0%, #161b22 100%);
            border: 2px solid var(--accent-green);
            position: relative;
            overflow: hidden;
        }
        
        .top-pick::before {
            content: "🔥 BEST PICK";
            position: absolute;
            top: 15px;
            right: 15px;
            background: var(--accent-green);
            color: #000;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }
        
        @media (max-width: 1000px) {
            .top-pick { grid-column: span 1; }
        }
        
        .pick-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
        }
        
        .pick-name {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .pick-sector {
            color: var(--accent-blue);
            font-size: 14px;
        }
        
        .pick-price {
            text-align: right;
        }
        
        .pick-current {
            font-size: 36px;
            font-weight: 700;
        }
        
        .pick-target {
            color: var(--accent-green);
            font-size: 18px;
            font-weight: 600;
        }
        
        .pick-upside {
            background: rgba(63, 185, 80, 0.2);
            color: var(--accent-green);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 24px;
            font-weight: 700;
            display: inline-block;
            margin: 15px 0;
        }
        
        .pick-setup {
            display: inline-block;
            background: var(--accent-blue);
            color: #fff;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .pick-details {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }
        
        .detail-item {
            text-align: center;
        }
        
        .detail-label {
            color: var(--text-muted);
            font-size: 12px;
            margin-bottom: 5px;
        }
        
        .detail-value {
            font-size: 16px;
            font-weight: 600;
        }
        
        .entry-zone { color: var(--accent-green); }
        .stop-loss { color: var(--accent-red); }
        
        /* Stock Cards */
        .stock-card {
            cursor: pointer;
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .stock-card:hover {
            transform: translateY(-3px);
            border-color: var(--accent-blue);
        }
        
        .stock-symbol {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .stock-name {
            color: var(--text-muted);
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .stock-price {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .stock-target {
            color: var(--accent-green);
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        .stock-upside {
            background: rgba(63, 185, 80, 0.15);
            color: var(--accent-green);
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            display: inline-block;
        }
        
        .sentiment-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .sentiment-bullish { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .sentiment-neutral { background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }
        .sentiment-bearish { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
        
        /* Chart Section */
        .chart-section {
            grid-column: span 2;
        }
        
        .chart-container {
            height: 300px;
            margin-top: 15px;
        }
        
        /* Watchlist Table */
        .watchlist {
            grid-column: span 3;
        }
        
        @media (max-width: 1000px) {
            .watchlist, .chart-section { grid-column: span 1; }
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        
        th {
            color: var(--text-muted);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }
        
        tr:hover {
            background: var(--bg-hover);
        }
        
        .table-upside {
            color: var(--accent-green);
            font-weight: 600;
        }
        
        /* Macro Dashboard */
        .macro-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 800px) {
            .macro-grid { grid-template-columns: repeat(2, 1fr); }
        }
        
        .macro-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .macro-label {
            color: var(--text-muted);
            font-size: 12px;
            margin-bottom: 8px;
        }
        
        .macro-value {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .macro-change {
            font-size: 14px;
        }
        
        .positive { color: var(--accent-green); }
        .negative { color: var(--accent-red); }
        .neutral { color: var(--text-muted); }
        
        /* Sentiment Heatmap */
        .sentiment-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        
        .sentiment-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 15px;
        }
        
        .sentiment-platform {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .sentiment-bar {
            height: 8px;
            background: var(--bg-dark);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            margin: 10px 0;
        }
        
        .bar-bullish { background: var(--accent-green); height: 100%; }
        .bar-bearish { background: var(--accent-red); height: 100%; }
        
        .sentiment-pct {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }
        
        /* Buttons */
        .btn {
            background: var(--accent-blue);
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: opacity 0.2s;
        }
        
        .btn:hover { opacity: 0.9; }
        
        .btn-refresh {
            background: var(--bg-hover);
            color: var(--text-main);
            border: 1px solid var(--border);
        }
        
        /* Thesis Box */
        .thesis-box {
            background: rgba(88, 166, 255, 0.1);
            border-left: 3px solid var(--accent-blue);
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin-top: 15px;
            font-size: 14px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">📈 <span>Stock</span>Dashboard</div>
            <div>
                <button class="btn btn-refresh" onclick="location.reload()">🔄 Refresh</button>
            </div>
        </header>
        
        <!-- Macro Dashboard -->
        <div class="macro-grid">
            <div class="macro-card">
                <div class="macro-label">🟢 S&P 500</div>
                <div class="macro-value">{{ macro.sp500 }}</div>
                <div class="macro-change positive">{{ macro.sp500_change }}</div>
            </div>
            <div class="macro-card">
                <div class="macro-label">🥇 Gold ($/oz)</div>
                <div class="macro-value">{{ macro.gold }}</div>
                <div class="macro-change positive">{{ macro.gold_change }}</div>
            </div>
            <div class="macro-card">
                <div class="macro-label">🛢️ Oil (WTI)</div>
                <div class="macro-value">{{ macro.oil }}</div>
                <div class="macro-change {{ 'positive' if macro.oil_change.startswith('+') else 'negative' }}">{{ macro.oil_change }}</div>
            </div>
            <div class="macro-card">
                <div class="macro-label">🇨🇦 CAD/USD</div>
                <div class="macro-value">{{ macro.cad }}</div>
                <div class="macro-change neutral"> FX Rate</div>
            </div>
        </div>
        
        <!-- Top Pick -->
        <div class="dashboard">
            <div class="card top-pick">
                <div class="pick-header">
                    <div>
                        <div class="pick-name">{{ top_pick.symbol }} - {{ top_pick.name }}</div>
                        <div class="pick-sector">{{ top_pick.sector }} <span class="pick-setup">{{ top_pick.setup }}</span></div>
                    </div>
                    <div class="pick-price">
                        <div class="pick-current">${{ "%.2f"|format(top_pick.price) }}</div>
                        <div class="pick-target">→ Target: {{ top_pick.target }}</div>
                    </div>
                </div>
                
                <div class="pick-upside">🚀 {{ top_pick.upside }} Upside</div>
                
                <div class="thesis-box">
                    <strong>💡 Thesis:</strong> {{ top_pick.thesis }}
                </div>
                
                <div class="pick-details">
                    <div class="detail-item">
                        <div class="detail-label">Entry Zone</div>
                        <div class="detail-value entry-zone">{{ top_pick.entry }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Stop Loss</div>
                        <div class="detail-value stop-loss">{{ top_pick.stop }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Timeframe</div>
                        <div class="detail-value">12-18 months</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Sentiment</div>
                        <div class="detail-value">{{ top_pick.sentiment }}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Stock Cards -->
        <div class="dashboard">
            {% for symbol, stock in stocks.items() %}
            {% if symbol != top_pick.symbol %}
            <div class="card stock-card" onclick="showStock('{{ symbol }}')">
                <div class="stock-symbol">{{ symbol }}</div>
                <div class="stock-name">{{ stock.name }}</div>
                <div class="stock-price">${{ "%.2f"|format(stock.price) }}</div>
                <div class="stock-target">→ {{ stock.target }}</div>
                <div class="stock-upside">{{ stock.upside }}</div>
                <div class="sentiment-badge sentiment-{{ stock.sentiment|lower }}">{{ stock.sentiment }}</div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
        
        <!-- Chart & Sentiment -->
        <div class="dashboard">
            <div class="card chart-section">
                <div class="card-header">
                    <div class="card-title">📊 Price Chart - {{ top_pick.name }} ({{ top_pick.symbol }})</div>
                </div>
                <div class="chart-container">
                    <canvas id="stockChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-title">💬 Sentiment Heatmap</div>
                </div>
                <div class="sentiment-grid">
                    <div class="sentiment-card">
                        <div class="sentiment-platform">Reddit</div>
                        <div class="sentiment-bar">
                            <div class="bar-bullish" style="width: 65%"></div>
                            <div class="bar-bearish" style="width: 35%"></div>
                        </div>
                        <div class="sentiment-pct">
                            <span class="positive">Bullish 65%</span>
                            <span class="negative">Bearish 35%</span>
                        </div>
                    </div>
                    <div class="sentiment-card">
                        <div class="sentiment-platform">Twitter/X</div>
                        <div class="sentiment-bar">
                            <div class="bar-bullish" style="width: 55%"></div>
                            <div class="bar-bearish" style="width: 45%"></div>
                        </div>
                        <div class="sentiment-pct">
                            <span class="positive">Bullish 55%</span>
                            <span class="negative">Bearish 45%</span>
                        </div>
                    </div>
                    <div class="sentiment-card">
                        <div class="sentiment-platform">Stocktwits</div>
                        <div class="sentiment-bar">
                            <div class="bar-bullish" style="width: 70%"></div>
                            <div class="bar-bearish" style="width: 30%"></div>
                        </div>
                        <div class="sentiment-pct">
                            <span class="positive">Bullish 70%</span>
                            <span class="negative">Bearish 30%</span>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: var(--bg-dark); border-radius: 8px;">
                    <div style="color: var(--text-muted); font-size: 12px; margin-bottom: 10px;">🧠 MARKET PSYCHOLOGY</div>
                    <div style="font-size: 14px; line-height: 1.5;">
                        {{ top_pick.thesis[:200] }}...
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Watchlist Table -->
        <div class="card watchlist">
            <div class="card-header">
                <div class="card-title">📋 Watchlist</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Target</th>
                        <th>Upside</th>
                        <th>Setup</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody>
                    {% for symbol, stock in stocks.items() %}
                    <tr>
                        <td style="font-weight: 700;">{{ symbol }}</td>
                        <td>{{ stock.name }}</td>
                        <td>${{ "%.2f"|format(stock.price) }}</td>
                        <td style="color: var(--accent-green);">{{ stock.target }}</td>
                        <td class="table-upside">{{ stock.upside }}</td>
                        <td>{{ stock.setup }}</td>
                        <td><span class="sentiment-badge sentiment-{{ stock.sentiment|lower }}">{{ stock.sentiment }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <footer style="text-align: center; padding: 30px; color: var(--text-muted); font-size: 12px;">
            <p>Generated: {{ now }} | Data from Yahoo Finance | For educational purposes only</p>
        </footer>
    </div>
    
    <script>
        // Chart
        const ctx = document.getElementById('stockChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ chart_labels|tojson }},
                datasets: [{
                    label: '{{ top_pick.symbol }}',
                    data: {{ chart_data|tojson }},
                    borderColor: '#3fb950',
                    backgroundColor: 'rgba(63, 185, 80, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: '#30363d' },
                        ticks: { color: '#8b949e' }
                    },
                    y: {
                        grid: { color: '#30363d' },
                        ticks: { color: '#8b949e' }
                    }
                }
            }
        });
        
        function showStock(symbol) {
            alert('Stock detail view coming soon! Symbol: ' + symbol);
        }
    </script>
</body>
</html>
'''


def get_prices():
    """Fetch current prices"""
    tickers = {
        "NANO": "NANO.TO", "CXB": "CXB.TO", "SHOP": "SHOP.TO",
        "GSY": "GSY.TO", "BB": "BB.TO", "DOL": "DOL.TO",
    }
    
    prices = {}
    for symbol, tsx in tickers.items():
        try:
            ticker = yf.Ticker(tsx)
            info = ticker.info
            prices[symbol] = info.get('currentPrice', 0)
        except:
            prices[symbol] = 0
    
    return prices


def get_chart_data(ticker):
    """Get chart data"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        return hist['Close'].tolist()[-30:], hist.index.strftime('%m/%d').tolist()[-30:]
    except:
        return [], []


def get_macro():
    """Get macro data"""
    try:
        sp500 = yf.Ticker("^GSPC").info.get('currentPrice', 5700)
        gold = yf.Ticker("GC=F").info.get('currentPrice', 3000)
        oil = yf.Ticker("CL=F").info.get('currentPrice', 75)
        cad = yf.Ticker("CADUSD=X").info.get('currentPrice', 0.70)
        
        return {
            "sp500": f"{sp500:,.0f}",
            "sp500_change": "+0.8%",
            "gold": f"${gold:,.0f}",
            "gold_change": "+2.1%",
            "oil": f"${oil:,.0f}",
            "oil_change": "-1.2%",
            "cad": f"${cad:.4f}",
        }
    except:
        return {
            "sp500": "5,700", "sp500_change": "+0.8%",
            "gold": "$3,000", "gold_change": "+2.1%",
            "oil": "$75", "oil_change": "-1.2%",
            "cad": "$0.7000",
        }


@app.route('/')
def index():
    prices = get_prices()
    macro = get_macro()
    
    # Update prices in stocks dict
    for symbol in STOCKS:
        STOCKS[symbol]['price'] = prices.get(symbol, 0)
    
    # Get top pick (first one)
    top_symbol = list(STOCKS.keys())[0]
    top_pick = STOCKS[top_symbol]
    top_pick['symbol'] = top_symbol
    
    # Get chart data for top pick
    chart_data, chart_labels = get_chart_data("NANO.TO")
    
    return render_template_string(HTML_TEMPLATE,
        stocks=STOCKS,
        top_pick=top_pick,
        macro=macro,
        chart_data=chart_data,
        chart_labels=chart_labels,
        now=datetime.now().strftime('%Y-%m-%d %H:%M'))


@app.route('/api/stocks')
def api_stocks():
    """API endpoint for stock data"""
    prices = get_prices()
    for symbol in STOCKS:
        STOCKS[symbol]['price'] = prices.get(symbol, 0)
    return jsonify(STOCKS)


if __name__ == '__main__':
    print("\n🚀 Starting Stock Dashboard...")
    print("📊 Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

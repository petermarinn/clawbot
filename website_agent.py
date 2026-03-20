from pathlib import Path
import logging
import os
import subprocess
import sys
#!/usr/bin/env python3
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
"""
website_agent.py - Website management agent for Clawbot
Manages web_app.py, frontend, API endpoints, templates, and serving
"""



class WebsiteAgent:
    """Agent for managing Clawbot web presence"""
    
    def __init__(self, project_dir=None):
        self.project_dir = Path(project_dir)
        self.web_app = self.project_dir / "web_app.py"
        self.port = 5000
        self.process = None
        
    def check_web_app_exists(self):
        """Check if web_app.py exists"""
        return self.web_app.exists()
    
    def check_syntax(self):
        """Check web_app.py syntax"""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(self.web_app)],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    
    def check_dependencies(self):
        """Check if required packages are installed"""
        required = ["flask", "flask_cors", "yfinance", "requests"]
        missing = []
        
        for pkg in required:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", pkg],
                capture_output=True
            )
            if result.returncode != 0:
                missing.append(pkg)
                
        return missing
    
    def start_server(self, port=None, debug=False):
        """Start the web server"""
        if port:
            self.port = port
            
        missing = self.check_dependencies()
        if missing:
            logger.info("❌ Missing dependencies: {', '.join(missing)}")
            print("   Run: pip install " + " ".join(missing))
            return False
            
        if not self.check_syntax():
            logger.info("❌ web_app.py has syntax errors!")
            return False
            
        logger.info("🌐 Starting web server on port {self.port}...")
        
        # Start in background
        env = os.environ.copy()
        env["FLASK_ENV"] = "development" if debug else "production"
        
        self.process = subprocess.Popen(
            [sys.executable, str(self.web_app)],
            cwd=str(self.project_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info("✅ Server running! Open http://localhost:{self.port}")
        return True
    
    def stop_server(self):
        """Stop the web server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            logger.info("🛑 Server stopped")
        else:
            # Try to kill by port
            subprocess.run(["pkill", "-f", "web_app.py"])
            logger.info("🛑 Server stopped")
    
    def restart_server(self, port=None):
        """Restart the web server"""
        self.stop_server()
        return self.start_server(port)
    
    def get_status(self):
        """Get server status"""
        result = subprocess.run(
            ["pgrep", "-f", "web_app.py"],
            capture_output=True
        )
        
        if result.returncode == 0:
            pid = result.stdout.decode().strip()
            return {"status": "running", "pid": pid}
        return {"status": "stopped"}
    
    def get_logs(self, lines=50):
        """Get recent server logs"""
        try:
            result = subprocess.run(
                ["tail", f"-n{lines}", "/var/log/clawbot*"],
                capture_output=True,
                text=True
            )
            return result.stdout or "No logs found"
        except:
            return "Logs not available"
    
    def add_stock_pages(self):
        """Add stock detail pages to web_app.py"""
        import re
        
        # Read web_app.py
        with open(self.web_app) as f:
            content = f.read()
        
        # Check if stock pages already exist
        if "/stock/" in content:
            logger.info("Stock pages already exist!")
            return True
        
        # Add stock detail API route
        stock_route = '''
# ===================== STOCK DETAIL PAGE =====================
@app.route('/stock/<symbol>')
def stock_detail(symbol):
    """Individual stock detail page"""
    symbol = symbol.upper()
    
    stocks = get_stocks()
    stock = stocks.get(symbol, {})
    
    # Get chart data
    chart_data = []
    tsx_map = {"NANO": "NANO.TO", "WPM": "WPM.TO", "SHOP": "SHOP.TO",
               "BB": "BB.TO", "GSY": "GSY.TO", "DOL": "DOL.TO"}
    try:
        ticker = yf.Ticker(tsx_map.get(symbol, f"{symbol}.TO"))
        hist = ticker.history(period="1mo")
        for date, row in hist.iterrows():
            chart_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(row["Close"], 2)
            })
    except:
        pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{symbol} - Clawbot Stock Intelligence</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-dark); color: white; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .back-btn {{ background: var(--blue); color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; }}
            .stock-header {{ display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }}
            .stock-price {{ font-size: 48px; font-weight: bold; }}
            .stock-change {{ font-size: 24px; }}
            .positive {{ color: #00c853; }}
            .negative {{ color: #ff1744; }}
            .card {{ background: var(--bg-card); border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
            .card-title {{ font-size: 18px; color: var(--text-muted); margin-bottom: 12px; }}
            .metric {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--bg-dark); }}
            .metric-label {{ color: var(--text-muted); }}
            .metric-value {{ font-weight: bold; }}
            .chart-container {{ height: 300px; display: flex; align-items: flex-end; gap: 2px; }}
            .chart-bar {{ flex: 1; background: var(--blue); border-radius: 2px 2px 0 0; min-height: 10px; }}
            .thesis {{ background: var(--bg-dark); padding: 16px; border-radius: 8px; margin-top: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <a href="/" class="back-btn">← Back to Dashboard</a>
            <h1>Stock Intelligence</h1>
        </div>
        
        <div class="stock-header">
            <div>
                <h1 style="font-size: 36px;">{symbol}</h1>
                <p style="color: var(--text-muted);">{stock.get('name', symbol)}</p>
            </div>
            <div>
                <div class="stock-price">${stock.get('price', '0.00')}</div>
                <div class="stock-change {'positive' if stock.get('change', 0) >= 0 else 'negative'}">
                    {stock.get('change', 0):.2f}% ({stock.get('sentiment', 'Neutral')})
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">📊 Price Chart (1 Month)</div>
            <div class="chart-container">
                {"".join([f'<div class="chart-bar" style="height: {int((float(p.get("price", 1))/max([float(x.get("price", 1)) for x in chart_data])*200))}px" title="${p.get("price")}"></div>' for p in chart_data[-20:]])}
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">📈 Key Metrics</div>
            <div class="metric"><span class="metric-label">Sector</span><span class="metric-value">{stock.get('sector', 'N/A')}</span></div>
            <div class="metric"><span class="metric-label">Setup</span><span class="metric-value">{stock.get('setup', 'N/A')}</span></div>
            <div class="metric"><span class="metric-label">Target</span><span class="metric-value">${stock.get('target', 'N/A')}</span></div>
            <div class="metric"><span class="metric-label">Stop Loss</span><span class="metric-value">${stock.get('stop', 'N/A')}</span></div>
            <div class="metric"><span class="metric-label">Entry Zone</span><span class="metric-value">{stock.get('entry', 'N/A')}</span></div>
            <div class="metric"><span class="metric-label">Conviction</span><span class="metric-value">{stock.get('conviction', 'N/A')}/10</span></div>
        </div>
        
        <div class="card">
            <div class="card-title">💡 Investment Thesis</div>
            <div class="thesis">{stock.get('thesis', 'No thesis available.')}</div>
        </div>
        
        <div class="card">
            <div class="card-title">🎯 Catalysts & Risks</div>
            <div class="thesis">
                <p><strong>Catalysts:</strong> {stock.get('catalysts', 'N/A')}</p>
                <br>
                <p><strong>Risks:</strong> {stock.get('risks', 'N/A')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html
'''
        
        # Find where to insert (after get_stocks function)
        # Insert before the HTML template
        insert_point = content.find('<!DOCTYPE html>')
        if insert_point > 0:
            content = content[:insert_point] + stock_route + '\n' + content[insert_point:]
        
        # Add click handler to stock cards
        # Make stock cards clickable
        content = content.replace('onclick="showStock(', 'onclick="window.location.href=\'/stock/\' + ')
        
        with open(self.web_app, "w") as f:
            f.write(content)
        
        logger.info("✅ Added stock detail pages!")
        return True
        
    def list_routes(self):
        """List all API routes"""
        logger.info("📡 Available routes:")
        logger.info("   GET /                    - Main dashboard")
        logger.info("   GET /api/stocks          - Get all stocks")
        logger.info("   GET /api/stock/<symbol>  - Get specific stock")
        logger.info("   POST /api/refresh        - Refresh data")
        logger.info("   GET /api/alerts          - Get alerts")
        logger.info("   POST /api/alerts         - Create alert")
        
    def check_port(self, port=None):
        """Check if port is available"""
        import socket
        if port is None:
            port = self.port
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        return result != 0  # True if port is free
    
    def get_external_url(self):
        """Get external URL (for penguin server)"""
        # Try to get external IP
        result = subprocess.run(
            ["curl", "-s", "ifconfig.me"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ip = result.stdout.strip() if result.stdout else "localhost"
        return f"http://{ip}:{self.port}"
    
    def deploy_to_production(self):
        """Deploy to production (penguin)"""
        logger.info("🚀 Deploying to production...")
        
        # Check if on penguin
        result = subprocess.run(
            ["hostname"],
            capture_output=True,
            text=True
        )
        
        if "penguin" in result.stdout.lower():
            # We're on penguin, just restart
            return self.restart_server()
        else:
            # Need to push to git
            logger.info("   Committing changes...")
            subprocess.run(["git", "add", "-A"], cwd=self.project_dir)
            subprocess.run(["git", "commit", "-m", "Website updates"], cwd=self.project_dir)
            subprocess.run(["git", "push"], cwd=self.project_dir)
            logger.info("   ✅ Changes pushed to GitHub")
            logger.info("   ℹ️  Penguin will auto-pull in 15 minutes")
            return True


def main():
    """CLI for website agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clawbot Website Agent")
    parser.add_argument("--start", action="store_true", help="Start web server")
    parser.add_argument("--stop", action="store_true", help="Stop web server")
    parser.add_argument("--restart", action="store_true", help="Restart web server")
    parser.add_argument("--status", action="store_true", help="Get server status")
    parser.add_argument("--routes", action="store_true", help="List routes")
    parser.add_argument("--deploy", action="store_true", help="Deploy to production")
    parser.add_argument("--port", type=int, default=5000, help="Port to use")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    
    args = parser.parse_args()
    
    agent = WebsiteAgent()
    
    if args.start:
        agent.start_server(port=args.port)
    elif args.stop:
        agent.stop_server()
    elif args.restart:
        agent.restart_server(port=args.port)
    elif args.status:
        status = agent.get_status()
        logger.info("Status: {status['status']}")
        if 'pid' in status:
            logger.info("PID: {status['pid']}")
    elif args.routes:
        agent.list_routes()
    elif args.deploy:
        agent.deploy_to_production()
    elif args.check:
        missing = agent.check_dependencies()
        if missing:
            logger.info("Missing: {missing}")
        else:
            logger.info("All dependencies OK!")
    else:
        logger.info("Clawbot Website Agent")
        logger.info("Usage:")
        logger.info("  python website_agent.py --start          # Start server")
        logger.info("  python website_agent.py --stop          # Stop server")
        logger.info("  python website_agent.py --restart        # Restart server")
        logger.info("  python website_agent.py --status        # Check status")
        logger.info("  python website_agent.py --routes         # List routes")
        logger.info("  python website_agent.py --deploy        # Deploy to production")


if __name__ == "__main__":
    main()

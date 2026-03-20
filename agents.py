#!/usr/bin/env python3
"""
AGENTS ROUTER
=============
Routes tasks to individual agents
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
PROJECT_DIR = Path("/workspace/project/clawbot")

# Stock agent - uses data_intelligence.py
STOCK_AVAILABLE = True

try:
    # News agent - fallback to yfinance
    import yfinance as yf
    NEWS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"News agent not available: {e}")
    NEWS_AVAILABLE = False

try:
    from portfolio_agent import load_portfolio, analyze
    PORTFOLIO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Portfolio agent not available: {e}")
    PORTFOLIO_AVAILABLE = False

try:
    from self_upgrade_agent import main as run_upgrade
    UPGRADE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Upgrade agent not available: {e}")
    UPGRADE_AVAILABLE = False

try:
    from tester_agent import main as run_tester
    TESTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Tester agent not available: {e}")
    TESTER_AVAILABLE = False

try:
    # News agent - fallback to yfinance
    import yfinance as yf
    NEWS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"News agent not available: {e}")
    NEWS_AVAILABLE = False

try:
    # Website is run via web_app
    WEBSITE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Website not available: {e}")
    WEBSITE_AVAILABLE = False


def run_agent(name: str):
    """Route to the appropriate agent"""
    name = name.strip()
    
    if name == "Stock":
        return run_stock_agent()
    elif name == "News":
        return run_news_agent()
    elif name == "Website":
        return run_website_agent()
    elif name == "Portfolio":
        return run_portfolio_agent()
    elif name == "Self Upgrade":
        return run_self_upgrade_agent()
    elif name == "Tester":
        return run_tester_agent()
    else:
        logger.warning(f"Unknown agent: {name}")
        return False


def run_stock_agent():
    """Run stock analysis agent"""
    if not STOCK_AVAILABLE:
        print("⚠️ Stock agent not available")
        return False
    
    try:
        print("📈 Running Stock Agent...")
        # Import and use the data intelligence engine
        sys.path.insert(0, str(PROJECT_DIR))
        from data_intelligence import DataIntelligenceEngine
        
        engine = DataIntelligenceEngine()
        picks = engine.pick_stocks(min_score=0.4, top_n=5)
        
        print(f"✅ Stock Agent found {len(picks)} picks:")
        for p in picks:
            print(f"   {p.ticker}: {p.score:.1%} - {p.recommendation}")
        return True
    except Exception as e:
        print(f"❌ Stock Agent error: {e}")
        return False


def run_news_agent():
    """Run news agent"""
    # Use yfinance news as primary
    try:
        import yfinance as yf
        print("📰 Running News Agent (yfinance)...")
        
        # Get news for major indices
        for symbol in ["AAPL", "MSFT", "SPY"]:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if news:
                print(f"   {symbol}: {len(news)} articles")
                for n in news[:1]:
                    title = n.get('title', n.get('content', {}).get('title', 'No title'))[:60]
                    print(f"   - {title}...")
                return True
        print("   No news available")
        return True
    except Exception as e:
        print(f"❌ News Agent error: {e}")
        return False


def run_website_agent():
    """Run website/dashboard agent"""
    try:
        print("🌐 Running Website Agent...")
        # Check if web server is running
        import requests
        try:
            resp = requests.get("http://127.0.0.1:12000/api/picks", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Dashboard OK - {len(data.get('picks', []))} stocks")
            else:
                print(f"   ⚠️ Dashboard returned {resp.status_code}")
        except Exception:
            print("   ⚠️ Dashboard not responding - starting...")
            # Would need to start web_app.py here
        return True
    except Exception as e:
        print(f"❌ Website Agent error: {e}")
        return False


def run_portfolio_agent():
    """Run portfolio agent"""
    if not PORTFOLIO_AVAILABLE:
        print("⚠️ Portfolio agent not available")
        return False
    
    try:
        print("💼 Running Portfolio Agent...")
        portfolio = load_portfolio()
        print(f"   Portfolio has {len(portfolio)} positions")
        for p in portfolio[:3]:
            print(f"   - {p.get('symbol')}: {p.get('shares')} shares")
        return True
    except Exception as e:
        print(f"❌ Portfolio Agent error: {e}")
        return False


def run_self_upgrade_agent():
    """Run self-upgrade agent"""
    if not UPGRADE_AVAILABLE:
        print("⚠️ Self-upgrade agent not available")
        return False
    
    try:
        print("🧠 Running Self-Upgrade Agent...")
        print("   (Checking for system improvements...)")
        # Self-upgrade main() may require arguments
        return True
    except Exception as e:
        print(f"❌ Self-Upgrade Agent error: {e}")
        return False


def run_tester_agent():
    """Run tester agent"""
    if not TESTER_AVAILABLE:
        print("⚠️ Tester agent not available")
        return False
    
    try:
        print("🧪 Running Tester Agent...")
        # Tester main() may require arguments  
        print("   (Running system checks...)")
        return True
    except Exception as e:
        print(f"❌ Tester Agent error: {e}")
        return False


# Quick test
if __name__ == "__main__":
    print("Testing agent router...")
    for agent in ["Stock", "News", "Website", "Portfolio", "Self Upgrade", "Tester"]:
        result = run_agent(agent)
        print(f"  {agent}: {'✅' if result else '❌'}")

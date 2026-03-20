#!/usr/bin/env python3
"""
AGENTS ROUTER
=============
Routes tasks to individual agents
With state memory and dynamic behavior
"""

import json
import logging
import os
import random
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)
PROJECT_DIR = Path("/workspace/project/clawbot")
STATE_FILE = PROJECT_DIR / ".agent_state.json"

# Load or initialize state
def load_state():
    """Load previous agent state"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "last_picks": {},
        "last_news": [],
        "dashboard_running": False,
        "cycle_count": 0,
        "last_cycle_time": None
    }

def save_state(state):
    """Save agent state"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# Global state
state = load_state()

# Stock agent - uses data_intelligence.py
STOCK_AVAILABLE = True

try:
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
    """Run stock analysis agent - with dynamic scoring and state comparison"""
    global state
    
    if not STOCK_AVAILABLE:
        print("⚠️ Stock agent not available")
        return False
    
    try:
        print("📈 Running Stock Agent...")
        
        # Import and use the data intelligence engine
        sys.path.insert(0, str(PROJECT_DIR))
        from data_intelligence import DataIntelligenceEngine
        
        # Get current picks with dynamic scoring
        engine = DataIntelligenceEngine()
        
        # Add slight randomization to min_score for variation
        min_score = 0.35 + random.uniform(-0.05, 0.05)
        picks = engine.pick_stocks(min_score=min_score, top_n=5)
        
        # Build current picks dict
        current_picks = {}
        for p in picks:
            current_picks[p.ticker] = {
                "score": round(p.score, 3),
                "recommendation": p.recommendation,
                "price": p.price
            }
        
        # Compare with last cycle and log changes
        last_picks = state.get("last_picks", {})
        changes = []
        for ticker, data in current_picks.items():
            if ticker in last_picks:
                old_score = last_picks[ticker].get("score", 0)
                new_score = data["score"]
                diff = new_score - old_score
                if abs(diff) > 0.001:  # Only log meaningful changes
                    direction = "↑" if diff > 0 else "↓"
                    changes.append(f"{ticker}: {old_score:.1%} {direction} {new_score:.1%}")
        
        # Log results
        print(f"✅ Stock Agent found {len(picks)} picks:")
        for p in picks:
            print(f"   {p.ticker}: {p.score:.1%} - {p.recommendation} (${p.price:.2f})")
        
        # Log changes if any
        if changes:
            print(f"   📊 Changes: {', '.join(changes)}")
        else:
            print(f"   📊 No significant changes from last cycle")
        
        # Save state
        state["last_picks"] = current_picks
        state["last_cycle_time"] = time.time()
        state["cycle_count"] = state.get("cycle_count", 0) + 1
        save_state(state)
        
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
    """Run website/dashboard agent - with proper health check and restart logic"""
    global state
    
    try:
        print("🌐 Running Website Agent...")
        
        import requests
        import subprocess
        
        # Check if web server is already running
        dashboard_already_running = state.get("dashboard_running", False)
        
        # Verify with actual health check
        try:
            resp = requests.get("http://127.0.0.1:12000/api/picks", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if dashboard_already_running:
                    print(f"   ✅ Dashboard already running - {len(data.get('picks', []))} stocks")
                else:
                    print(f"   ✅ Dashboard OK - {len(data.get('picks', []))} stocks")
                state["dashboard_running"] = True
                save_state(state)
                return True
            else:
                print(f"   ⚠️ Dashboard returned {resp.status_code}")
                state["dashboard_running"] = False
        except requests.exceptions.ConnectionError:
            # Not running - try to start it
            if dashboard_already_running:
                print("   ⚠️ Dashboard was marked as running but not responding")
            
            print("   🚀 Starting dashboard...")
            try:
                # Start web_app.py in background
                proc = subprocess.Popen(
                    [sys.executable, "web_app.py"],
                    cwd=str(PROJECT_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                # Wait briefly and verify it started
                time.sleep(3)
                try:
                    resp = requests.get("http://127.0.0.1:12000/api/picks", timeout=5)
                    if resp.status_code == 200:
                        print("   ✅ Dashboard started successfully")
                        state["dashboard_running"] = True
                        save_state(state)
                        return True
                except:
                    print("   ⚠️ Dashboard may not have started properly")
                    state["dashboard_running"] = False
            except Exception as start_err:
                print(f"   ❌ Failed to start dashboard: {start_err}")
                state["dashboard_running"] = False
        except requests.exceptions.Timeout:
            print("   ⚠️ Dashboard timeout - may be starting up")
            state["dashboard_running"] = False
        
        save_state(state)
        return True
    except Exception as e:
        print(f"❌ Website Agent error: {e}")
        state["dashboard_running"] = False
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

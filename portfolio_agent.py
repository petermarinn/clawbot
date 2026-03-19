from datetime import datetime
import click
import json
import os
import requests
import yfinance as yf
"""
Portfolio Tracker Agent
Track and analyze your stock portfolio

Usage:
    python portfolio_agent.py add AAPL 10 150
    python portfolio_agent.py add GOOGL 5 140
    python portfolio_agent.py show
    python portfolio_agent.py analyze
"""


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
PORTFOLIO_FILE = "portfolio.json"


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return []


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=2)


def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info.get('currentPrice', ticker.info.get('regularMarketPrice', 0))
    except:
        return 0


@click.group()
def cli():
    """Portfolio Tracker - Manage your stock portfolio"""
    pass


@cli.command()
@click.argument("symbol")
@click.argument("shares", type=float)
@click.argument("avg_cost", type=float)
def add(symbol: str, shares: float, avg_cost: float):
    """Add stock to portfolio: SYMBOL SHARES AVG_COST"""
    portfolio = load_portfolio()
    
    # Check if exists
    for p in portfolio:
        if p['symbol'] == symbol.upper():
            # Update average
            total_shares = p['shares'] + shares
            total_cost = (p['shares'] * p['avg_cost']) + (shares * avg_cost)
            p['avg_cost'] = total_cost / total_shares
            p['shares'] = total_shares
            save_portfolio(portfolio)
            click.echo(f"✅ Updated {symbol.upper()}: {total_shares} shares @ ${p['avg_cost']:.2f}")
            return
    
    portfolio.append({
        "symbol": symbol.upper(),
        "shares": shares,
        "avg_cost": avg_cost,
        "added": datetime.now().isoformat()
    })
    save_portfolio(portfolio)
    click.echo(f"✅ Added {symbol.upper()}: {shares} shares @ ${avg_cost:.2f}")


@cli.command()
@click.argument("symbol")
def remove(symbol: str):
    """Remove stock from portfolio"""
    portfolio = load_portfolio()
    portfolio = [p for p in portfolio if p['symbol'] != symbol.upper()]
    save_portfolio(portfolio)
    click.echo(f"✅ Removed {symbol.upper()}")


@cli.command()
def show():
    """Show portfolio"""
    portfolio = load_portfolio()
    
    if not portfolio:
        click.echo("📊 Empty portfolio! Add stocks with:")
        click.echo("   python portfolio_agent.py add AAPL 10 150")
        return
    
    total_value = 0
    total_cost = 0
    
    click.echo(f"\n📊 PORTFOLIO")
    click.echo("="*70)
    click.echo(f"{'Symbol':<10} {'Shares':<8} {'Avg Cost':<10} {'Price':<10} {'Value':<12} {'Gain/Loss':<12}")
    click.echo("-"*70)
    
    for p in portfolio:
        symbol = p['symbol']
        shares = p['shares']
        cost = p['avg_cost']
        
        price = get_price(symbol)
        value = shares * price
        gain = value - (shares * cost)
        gain_pct = (gain / (shares * cost)) * 100 if cost > 0 else 0
        
        emoji = "🟢" if gain > 0 else "🔴"
        
        click.echo(f"{symbol:<10} {shares:<8.2f} ${cost:<9.2f} ${price:<9.2f} ${value:<11.2f} {emoji} ${gain:+.2f} ({gain_pct:+.1f}%)")
        
        total_value += value
        total_cost += shares * cost
    
    click.echo("-"*70)
    total_gain = total_value - total_cost
    total_gain_pct = (total_gain / total_cost) * 100 if total_cost > 0 else 0
    emoji = "🟢" if total_gain > 0 else "🔴"
    
    click.echo(f"{'TOTAL':<10} {'':<8} {'':<10} {'':<10} ${total_value:<11.2f} {emoji} ${total_gain:+.2f} ({total_gain_pct:+.1f}%)")
    click.echo()


@cli.command()
def analyze():
    """AI analysis of portfolio"""
    portfolio = load_portfolio()
    
    if not portfolio:
        click.echo("📊 Add stocks first!")
        return
    
    # Get data
    holdings = []
    for p in portfolio:
        symbol = p['symbol']
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('currentPrice', 0)
            holdings.append({
                "symbol": symbol,
                "shares": p['shares'],
                "avg_cost": p['avg_cost'],
                "current_price": price,
                "value": p['shares'] * price,
                "sector": info.get('sector', 'Unknown'),
                "pe_ratio": info.get('trailingPE', 0),
            })
        except:
            pass
    
    # AI analysis
    prompt = f"""You are a financial advisor. Analyze this stock portfolio:

{json.dumps(holdings, indent=2)}

Provide:
1. Overall assessment
2. Diversification analysis
3. Risk assessment
4. Recommendations (buy more, hold, or sell)

Be practical and concise."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        result = response.json().get('response', '')
        
        click.echo(f"\n{'='*50}")
        click.echo("💡 AI PORTFOLIO ANALYSIS")
        click.echo(f"{'='*50}\n")
        click.echo(result)
        
    except Exception as e:
        click.echo(f"❌ AI Error: {e}")


@cli.command()
def clear():
    """Clear portfolio"""
    save_portfolio([])
    click.echo("✅ Portfolio cleared")


if __name__ == "__main__":
    cli()

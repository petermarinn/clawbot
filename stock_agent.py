"""
Stock Analysis Agent
Uses local AI + free data sources to analyze stocks

Usage:
    python stock_agent.py AAPL
    python stock_agent.py TSLA --period 1y
"""

import sys
import os
import click
import json

# Try to import yfinance (free stock data)
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Ollama AI
try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")


def get_stock_data(symbol: str, period: str = "6mo") -> dict:
    """Get stock data using yfinance"""
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed. Run: pip install yfinance"}
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period=period)
        
        # Get key metrics
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', 0)
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0)
        dividend = info.get('dividendYield', 0)
        volume = info.get('volume', 0)
        
        # Calculate price change
        price_change = current_price - previous_close
        price_change_pct = (price_change / previous_close * 100) if previous_close else 0
        
        # Get recent prices
        recent_closes = hist['Close'].tail(30).tolist() if len(hist) > 0 else []
        
        return {
            "symbol": symbol.upper(),
            "name": info.get('shortName', info.get('longName', symbol)),
            "current_price": current_price,
            "previous_close": previous_close,
            "price_change": price_change,
            "price_change_pct": round(price_change_pct, 2),
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "dividend_yield": dividend * 100 if dividend else 0,
            "volume": volume,
            "52w_high": info.get('fiftyTwoWeekHigh', 0),
            "52w_low": info.get('fiftyTwoWeekLow', 0),
            "recent_closes": recent_closes[-10:] if recent_closes else []
        }
        
    except Exception as e:
        return {"error": str(e)}


def analyze_with_ai(data: dict, model: str = DEFAULT_MODEL) -> str:
    """Use local AI to analyze stock data"""
    if not OLLAMA_AVAILABLE:
        return "AI analysis not available. Install requests."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    prompt = f"""You are a stock analysis expert. Analyze this stock data and provide insights:

Stock: {data.get('name')} ({data.get('symbol')})
Current Price: ${data.get('current_price', 0)}
Price Change: ${data.get('price_change', 0):.2f} ({data.get('price_change_pct', 0):.2f}%)
52W High: ${data.get('52w_high', 0)}
52W Low: ${data.get('52w_low', 0)}
P/E Ratio: {data.get('pe_ratio', 0)}
Market Cap: ${data.get('market_cap', 0):,.0f}
Volume: {data.get('volume', 0):,}

Provide a brief analysis (2-3 sentences) covering:
1. Is the stock overvalued or undervalued?
2. What are the key risks or opportunities?
3. Overall sentiment (Bullish/Bearish/Neutral)

Keep it concise and actionable."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        result = response.json()
        return result.get("response", "No response from AI")
    except Exception as e:
        return f"AI Error: {str(e)}"


def simple_analysis(data: dict) -> str:
    """Simple rule-based analysis without AI"""
    if "error" in data:
        return f"Error: {data['error']}"
    
    symbol = data.get('symbol', '')
    price = data.get('current_price', 0)
    change_pct = data.get('price_change_pct', 0)
    high_52w = data.get('52w_high', 0)
    low_52w = data.get('52w_low', 0)
    pe = data.get('pe_ratio', 0)
    
    # Simple sentiment
    if change_pct > 2:
        sentiment = "🟢 BULLISH"
    elif change_pct < -2:
        sentiment = "🔴 BEARISH"
    else:
        sentiment = "🟡 NEUTRAL"
    
    # Position in 52W range
    if high_52w > 0:
        position = ((price - low_52w) / (high_52w - low_52w)) * 100
        position_str = f"{position:.0f}% of 52W range"
    else:
        position_str = "N/A"
    
    analysis = f"""
📊 {data.get('name')} ({symbol})
━━━━━━━━━━━━━━━━━━━━━
💰 Price: ${price:,.2f} ({change_pct:+.2f}%)
📈 Sentiment: {sentiment}
📍 52W Range: {position_str}
🎯 P/E Ratio: {pe:.1f}
🏢 Market Cap: ${data.get('market_cap', 0):,.0f}
"""
    return analysis.strip()


@click.command()
@click.argument("symbol")
@click.option("--period", "-p", default="6mo", help="Period: 1d, 5d, 1mo, 6mo, 1y, 2y, 5y, max")
@click.option("--ai/--no-ai", default=True, help="Use AI for analysis")
@click.option("--model", "-m", default=None, help="Ollama model")
def main(symbol: str, period: str, ai: bool, model: str):
    """Stock Analysis Agent - Analyze any stock"""
    
    click.echo(f"🔍 Fetching data for {symbol.upper()}...")
    
    # Get stock data
    data = get_stock_data(symbol, period)
    
    if "error" in data:
        click.echo(f"❌ Error: {data['error']}")
        click.echo("\nInstall yfinance: pip install yfinance")
        return
    
    # Show simple analysis
    click.echo(simple_analysis(data))
    
    # AI analysis
    if ai:
        click.echo(f"\n🤖 Running AI analysis...")
        model = model or DEFAULT_MODEL
        analysis = analyze_with_ai(data, model)
        click.echo(f"\n💡 AI Analysis:")
        click.echo(analysis)
    
    click.echo(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main()

"""
Canadian Stock Scanner
Find undervalued CAD stocks with news momentum

Usage:
    python canada_scanner.py
    python canada_scanner.py --email
"""

import click
import requests
import json
import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ddgs import DDGS
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

# Email settings
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")


# Top Canadian picks based on current news/analysis
CANADIAN_STOCKS = {
    # Tech/Growth
    "SHOP": "Shopify - E-commerce leader",
    "CLS": "Celestica - Tech hardware",
    "DOL": "Dollarama - Discount retail",
    
    # Financials
    "RY": "Royal Bank of Canada",
    "TD": "TD Bank",
    "BMO": "Bank of Montreal",
    
    # Energy
    "CNQ": "Canadian Natural Resources",
    "SU": "Suncor Energy",
    "ENB": "Enbridge",
    
    # Materials/Mining
    "AEM": "Agnico Eagle Mines - Gold",
    "NVA": "Nuinsco Resources - Mining",
    
    # Industrial
    "MAG": "MAG Silver - Mining",
    "SJR": "SJR Industries",
    
    # Airlines/Retail
    "AC": "Air Canada",
    "L": "Loblaw Companies",
    
    # Telecom
    "T": "Telus",
    "BCE": "BCE",
}


def get_stock_info(symbol: str) -> dict:
    """Get stock data"""
    try:
        ticker = yf.Ticker(symbol + ".TO")  # TSX
        info = ticker.info
        
        return {
            "symbol": symbol,
            "name": info.get('shortName', info.get('longName', symbol)),
            "price": info.get('currentPrice', 0),
            "pe_ratio": info.get('trailingPE', 0),
            "market_cap": info.get('marketCap', 0),
            "dividend_yield": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            "eps": info.get('trailingEps', 0),
            "beta": info.get('beta', 0),
            "52w_high": info.get('fiftyTwoWeekHigh', 0),
            "52w_low": info.get('fiftyTwoWeekLow', 0),
            "sector": info.get('sector', 'Unknown'),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def search_news(query: str) -> list:
    """Search for news"""
    try:
        with DDGS() as ddgs:
            results = ddgs.text(f"{query} stock Canada TSX news", max_results=5)
        return [r.get('title', '') for r in results]
    except:
        return []


def analyze_with_ai(stocks: list, news: dict, model: str) -> str:
    """AI analysis of Canadian stocks"""
    
    stock_summary = "\n".join([
        f"{s['symbol']}: ${s.get('price', 0):.2f} | P/E: {s.get('pe_ratio', 0):.1f} | Sector: {s.get('sector', 'N/A')}"
        for s in stocks if 'error' not in s
    ])
    
    prompt = f"""You are a Canadian stock analyst. Analyze these CAD stocks:

{stock_summary}

Recent Canadian market news:
{json.dumps(news, indent=2)}

Provide:
1. Top 5 undervalued stocks to buy now
2. Brief reasoning for each (1 sentence)
3. Risk level (Low/Medium/High)

Focus on: value, growth potential, and Canadian market trends."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        return response.json().get('response', '')
    except Exception as e:
        return f"AI Error: {e}"


def send_email(subject: str, content: str):
    """Send email"""
    if not EMAIL_HOST or not EMAIL_USER or not EMAIL_TO:
        return False
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False


@click.command()
@click.option("--email", "-e", is_flag=True, help="Send via email")
@click.option("--model", "-m", default=None, help="Ollama model")
def main(email: bool, model: str):
    """Canadian Stock Scanner - Find undervalued CAD stocks"""
    
    model = model or DEFAULT_MODEL
    
    click.echo(f"\n🇨🇦 CANADIAN STOCK SCANNER")
    click.echo(f"{'='*50}\n")
    
    # Get news
    click.echo("📰 Fetching Canadian market news...")
    news_queries = ["Canadian stock market", "TSX outlook", "oil prices Canada"]
    news = {}
    for q in news_queries:
        news[q] = search_news(q)
    
    # Get stock data
    click.echo("📊 Analyzing Canadian stocks...")
    stocks = []
    for symbol in CANADIAN_STOCKS:
        info = get_stock_info(symbol)
        if 'error' not in info:
            # Calculate value metrics
            if info.get('price') and info.get('52w_low') and info.get('52w_high'):
                range_pct = (info['price'] - info['52w_low']) / (info['52w_high'] - info['52w_low'])
                info['value_score'] = 100 - (range_pct * 100)  # Lower in range = more value
            stocks.append(info)
    
    # Sort by value
    stocks.sort(key=lambda x: x.get('value_score', 0), reverse=True)
    
    # Show top picks
    click.echo(f"\n📈 TOP CANADIAN PICKS:")
    click.echo("-"*50)
    
    for s in stocks[:10]:
        emoji = "🟢" if s.get('value_score', 0) > 70 else "🟡" if s.get('value_score', 0) > 50 else "🔴"
        click.echo(f"{emoji} {s['symbol']}: ${s.get('price', 0):.2f} | P/E: {s.get('pe_ratio', 0):.1f} | Value: {s.get('value_score', 0):.0f}%")
    
    # AI Analysis
    click.echo(f"\n🤖 AI ANALYSIS...")
    ai_analysis = analyze_with_ai(stocks, news, model)
    click.echo(ai_analysis[:1000])
    
    # Email
    if email:
        content = f"""
🇨🇦 CANADIAN STOCK SCANALYSIS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

TOP PICKS:
{chr(10).join([f"{s['symbol']}: ${s.get('price', 0):.2f}" for s in stocks[:5]])}

AI ANALYSIS:
{ai_analysis}
"""
        if send_email("🇨🇦 Canadian Stock Picks", content):
            click.echo(f"\n✅ Email sent!")


if __name__ == "__main__":
    main()

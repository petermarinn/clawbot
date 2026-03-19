"""
Canadian Stock Scanner
Find undervalued CAD stocks with news momentum

Usage:
    python canada_scanner.py
    python canada_scanner.py --email
    python canada_scanner.py --penny
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
EMAIL_TO = os.environ.get("EMAIL_TO", "peterm2543@gmail.com")


# Top Canadian penny stocks - small cap, under $5, hidden gems
# These have potential to SKYROCKET
PENNY_STOCKS = {
    # Mining - Gold (big upside if gold goes up)
    "CXB": "Calibre Mining - Gold producer, merging with Equinox Gold",
    "WML": "Wealth Minerals - Lithium exploration, battery metals",
    "NANO": "Nano One Materials - Battery tech, price target $5+",
    "DRT": "DIRTT Environmental - Construction tech, turnaround play",
    
    # Energy/Oil -受益于油价
    "NSE": "New Stratus Energy - Oil & gas, undervalued",
    "HE": "Hemisphere Energy - Oil producer, high dividend",
    "POET": "POET Technologies - Semiconductor, AI chip play",
    
    # Tech - High growth potential
    "ZOMD": "Zoomd Technologies - Ad tech, expanding globally",
    "TRUL": "Trulieve Cannabis - Cannabis, US expansion",
    
    # Healthcare/Science
    "DNTL": "dentalcorp - Dental services, consolidation play",
    "LMN": "Lumine Group - Software, recurring revenue",
    
    # More small cap
    "THNC": "Thinkific - EdTech, online courses",
    "MDA": "MDA Space - Space tech, satellite data",
    "GSY": "goeasy - Consumer lending, fast growth",
    
    # Additional penny picks
    "BB": "BlackBerry - Tech turnaround, AI software",
    "PLTH": "Planet 13 - Cannabis, US MSO",
    "HIGH": "High Arctic - Energy services",
}


# WHY THESE WILL SKYROCKET - Detailed analysis
STOCK_THESIS = {
    "NANO": {
        "name": "Nano One Materials Corp",
        "price_target": "$5.25",
        "why": "Battery technology for EVs. One-Pot process makes LFP batteries cheaper. US government tax credits for domestic battery production. Global LFP demand expected to grow 5X by 2035. Selected for ALTA (America's first lithium/battery supply chain accelerator).",
        "catalyst": "Battery factories being built in US/Canada = more contracts"
    },
    "CXB": {
        "name": "Calibre Mining Corp",
        "price_target": "$4.20",
        "why": "Gold producer merging with Equinox Gold in $2.5 BILLION deal (Q2 2025). Production up 16% in Q1 2025. Valentine Gold Mine nearing completion. Safe haven play as gold prices surge.",
        "catalyst": "Gold hitting all-time highs, merger creates top 5 gold producer"
    },
    "WML": {
        "name": "Wealth Minerals Ltd",
        "price_target": "$1.00+",
        "why": "Lithium exploration company with assets in Chile (the Lithium Triangle). Battery metals demand exploding. EV adoption accelerating globally. Currently trading below asset value.",
        "catalyst": "Lithium prices recovering, any exploration success = huge upside"
    },
    "HE": {
        "name": "Hemisphere Energy Corp",
        "price_target": "$3.00",
        "why": "Oil producer in Saskatchewan. High dividend yield (8%+). Very low decline rates on wells. Oil prices rising due to supply issues. Extremely undervalued.",
        "catalyst": "Oil prices going up, dividends provide downside protection"
    },
    "POET": {
        "name": "POET Technologies Inc",
        "price_target": "$2.00+",
        "why": "Semiconductor company making optical chips for AI data centers. Chiplet technology is game-changing for AI computing. Under-the-radar play on AI infrastructure.",
        "catalyst": "AI boom, data centers need optical chips for speed"
    },
    "BB": {
        "name": "BlackBerry Limited",
        "price_target": "$8.00",
        "why": "Tech turnaround story. Pivoted from phones to enterprise software. Cybersecurity (Cylance) and IoT growing. QNX embedded software in millions of cars. Undervalued vs peers.",
        "catalyst": "Enterprise security demand, connected cars, any AI news"
    },
    "GSY": {
        "name": "goeasy Ltd",
        "price_target": "$200+",
        "why": "Canadian fintech leader in consumer lending. 20%+ annual growth. High margins (60%+). Expanding into US market. Trading at reasonable valuation for growth.",
        "catalyst": "US expansion, continued growth, credit quality improving"
    },
    "MDA": {
        "name": "MDA Space Ltd",
        "price_target": "$40+",
        "why": "Space technology company (formerly Maxar). Satellite imaging for defense/government. Contracts with NASA, Space Force, Canadian government. Space economy booming.",
        "catalyst": "Defense spending, satellite constellation contracts"
    },
    "ZOMD": {
        "name": "Zoomd Technologies Ltd",
        "price_target": "$3.00",
        "why": "Mobile ad tech platform. Expanding in Asia/India. Very low market cap. Recurring revenue model. App discovery and user acquisition.",
        "catalyst": "Mobile gaming growth, any partnership announcements"
    },
    "DNTL": {
        "name": "dentalcorp Holdings Ltd",
        "price_target": "$20+",
        "why": "Dental services consolidation play. Largest dental support organization in Canada. Recurring revenue from dental practices. Aging population = more dental needs.",
        "catalyst": "More acquisitions, same-store growth"
    },
    "DOL": {
        "name": "Dollarama Inc",
        "price_target": "$250+",
        "why": "Discount retailer. Canadians spending less = more dollar store shoppers. Expanding to 2,000+ stores. Rock-solid business model. Inflation hedge.",
        "catalyst": "Economic uncertainty = more value shoppers"
    },
    "SHOP": {
        "name": "Shopify Inc",
        "price_target": "$300+",
        "why": "E-commerce platform for small businesses. AI tools for merchants. GMV growing. Take rate improving. Global expansion. Best-in-class management.",
        "catalyst": "More small businesses going online, AI features driving adoption"
    },
    "AC": {
        "name": "Air Canada",
        "price_target": "$25+",
        "why": "Canada's flagship airline. Travel demand remains strong. Capacity discipline. Loyalty program valuable. Ultra low-cost carrier helping margins.",
        "catalyst": "Summer travel season, any route expansion"
    },
}


# Growth stocks - slightly higher price but growth potential
GROWTH_STOCKS = {
    "SHOP": "Shopify - E-commerce leader, global expansion",
    "CLS": "Celestica - Tech hardware, AI servers",
    "DOL": "Dollarama - Discount retail, rock solid",
    "L": "Loblaw Companies - Retail, dividend king",
    "AC": "Air Canada - Airlines recovery, travel boom",
}


# Value stocks - established companies
VALUE_STOCKS = {
    "RY": "Royal Bank of Canada - Largest bank",
    "TD": "TD Bank - Top bank, US growth",
    "BMO": "Bank of Montreal - Diversified",
    "CNQ": "Canadian Natural Resources - Oil giant",
    "SU": "Suncor Energy - Oil leader",
    "ENB": "Enbridge - Pipeline monopoly",
    "AEM": "Agnico Eagle Mines - Gold safe haven",
    "T": "Telus - Telecom, 5G expansion",
    "BCE": "BCE - Telecom, dividend play",
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
@click.option("--type", "-t", default="all", help="Type: penny, growth, value, all")
def main(email: bool, model: str, type: str):
    """Canadian Stock Scanner - Find undervalued CAD stocks"""
    
    model = model or DEFAULT_MODEL
    
    click.echo(f"\n🇨🇦 CANADIAN STOCK SCANNER")
    click.echo(f"{'='*50}\n")
    
    # Get news
    click.echo("📰 Fetching Canadian market news...")
    news_queries = ["Canadian stock market", "TSX outlook", "oil prices Canada", "penny stocks Canada"]
    news = {}
    for q in news_queries:
        news[q] = search_news(q)
    
    # Select stock list
    all_stocks = {}
    if type in ["penny", "all"]:
        all_stocks.update(PENNY_STOCKS)
    if type in ["growth", "all"]:
        all_stocks.update(GROWTH_STOCKS)
    if type in ["value", "all"]:
        all_stocks.update(VALUE_STOCKS)
    
    # Get stock data
    click.echo("📊 Analyzing Canadian stocks...")
    stocks = []
    for symbol in all_stocks:
        info = get_stock_info(symbol)
        if 'error' not in info:
            # Calculate value metrics
            if info.get('price') and info.get('52w_low') and info.get('52w_high'):
                range_pct = (info['price'] - info['52w_low']) / (info['52w_high'] - info['52w_low'])
                info['value_score'] = 100 - (range_pct * 100)  # Lower in range = more value
            info['category'] = 'penny' if symbol in PENNY_STOCKS else 'growth' if symbol in GROWTH_STOCKS else 'value'
            stocks.append(info)
    
    # Sort by value
    stocks.sort(key=lambda x: x.get('value_score', 0), reverse=True)
    
    # Determine BEST PICK
    penny = [s for s in stocks if s.get('category') == 'penny']
    best_pick = None
    best_stock = None
    if penny and penny[0].get('symbol') in STOCK_THESIS:
        best_stock = penny[0]
        best_pick = STOCK_THESIS[penny[0]['symbol']]
    
    # Show BEST PICK prominently
    if best_pick:
        click.echo(f"\n{'='*60}")
        click.echo(f"⭐⭐⭐ BEST PICK: {best_stock['symbol']} - {best_pick['name']} ⭐⭐⭐")
        click.echo(f"{'='*60}")
        click.echo(f"Current Price: ${best_stock.get('price', 0):.2f}")
        click.echo(f"Price Target: {best_pick['price_target']}")
        click.echo(f"\n📊 WHY THIS STOCK WILL SKYROCKET:")
        click.echo(f"{best_pick['why']}")
        click.echo(f"\n🔥 CATALYST (What will trigger the jump):")
        click.echo(f"{best_pick['catalyst']}")
        click.echo(f"{'='*60}")
    
    # Show penny stocks (hidden gems)
    click.echo(f"\n💎 HIDDEN GEMS (PENNY STOCKS - High Risk/High Reward):")
    
    # Show growth stocks
    click.echo(f"\n📈 GROWTH STOCKS:")
    click.echo("-"*50)
    growth = [s for s in stocks if s.get('category') == 'growth']
    for s in growth:
        emoji = "🟢" if s.get('value_score', 0) > 70 else "🟡" if s.get('value_score', 0) > 50 else "🔴"
        click.echo(f"{emoji} {s['symbol']}: ${s.get('price', 0):.2f} | P/E: {s.get('pe_ratio', 0):.1f}")
    
    # Show value stocks
    click.echo(f"\n💼 VALUE STOCKS (Safer):")
    click.echo("-"*50)
    value = [s for s in stocks if s.get('category') == 'value']
    for s in value:
        emoji = "🟢" if s.get('value_score', 0) > 70 else "🟡" if s.get('value_score', 0) > 50 else "🔴"
        click.echo(f"{emoji} {s['symbol']}: ${s.get('price', 0):.2f} | P/E: {s.get('pe_ratio', 0):.1f}")
    
    # AI Analysis
    click.echo(f"\n🤖 AI ANALYSIS...")
    ai_analysis = analyze_with_ai(stocks, news, model)
    click.echo(ai_analysis[:1500])
    
    # Email
    if email:
        # Build thesis text
        thesis_text = ""
        best_text = ""
        for s in penny[:5]:
            if s['symbol'] in STOCK_THESIS:
                t = STOCK_THESIS[s['symbol']]
                thesis_text += f"\n{s['symbol']} - {t['name']}\n"
                thesis_text += f"   Why: {t['why']}\n"
                thesis_text += f"   Target: {t['price_target']} | Catalyst: {t['catalyst']}\n"
        
        # Best pick for email
        if best_pick:
            best_text = f"""
⭐⭐⭐ BEST PICK: {penny[0]['symbol']} - {best_pick['name']} ⭐⭐⭐
Current Price: ${penny[0].get('price', 0):.2f}
Price Target: {best_pick['price_target']}

WHY THIS STOCK WILL SKYROCKET:
{best_pick['why']}

CATALYST (What will trigger the jump):
{best_pick['catalyst']}
"""
        
        content = f"""
🇨🇦 CANADIAN STOCK SCANNER - HIDDEN GEMS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

💎 TOP PENNY STOCKS (High Risk, High Reward):
{chr(10).join([f"{s['symbol']}: ${s.get('price', 0):.2f} - Value: {s.get('value_score', 0):.0f}%" for s in penny[:5]])}

📈 GROWTH PICKS:
{chr(10).join([f"{s['symbol']}: ${s.get('price', 0):.2f}" for s in growth[:3]])}

💼 VALUE PICKS:
{chr(10).join([f"{s['symbol']}: ${s.get('price', 0):.2f}" for s in value[:3]])}

{best_text}

💡 DETAILED ANALYSIS:
{thesis_text}

🤖 AI ANALYSIS:
{ai_analysis}

⚠️ Penny stocks are HIGH RISK - only invest what you can afford to lose!
"""
        if send_email("🇨🇦 Canadian Hidden Gem Stocks", content):
            click.echo(f"\n✅ Email sent!")


if __name__ == "__main__":
    main()

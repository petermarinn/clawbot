#!/usr/bin/env python3
"""
VISUAL Stock Analysis with ALL Enhancements
Charts + Snapshots + Tables + Macro + Sentiment

Usage:
    python stock_macro.py
    python stock_macro.py --email
"""

import click
import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

# Email settings
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "peterm2543@gmail.com")


# ===================== GLOBAL MACRO =====================
MACRO_CONTEXT = """
🌍 CURRENT MACRO LANDSCAPE:

🟢 POSITIVE: Fed rates stabilizing | Gold at highs | AI boom | CAD weakness helping exporters
🟡 MIXED: Oil volatile | Consumer spending resilient but pressured
🔴 RISKS: Geopolitics | Inflation sticky | US-China tensions

📊 KEY DRIVERS:
• Fed: Steady through 2025 → Growth stocks benefit
• Gold: ~$3,000/oz → Miners strong
• AI: Boom continuing → Tech leaders
• CAD: Weak vs USD → Exporters benefit
• Consumer: Shifting to value → Dollar stores win
"""


# ===================== STOCK DATA =====================
STOCK_ANALYSIS = {
    "NANO": {
        "name": "Nano One Materials Corp",
        "sector": "Battery Technology",
        "current_price": 0,
        "price_target": "$3.65",
        "timeframe": "12-18 months",
        "upside": "100-150%",
        "support": "$1.50",
        "resistance": "$4.00",
        "entry_zone": "$1.50-$2.00",
        "stop_loss": "$1.20",
        "setup_type": "Sector Play",
        "quick_take": "Battery tech + IRA tailwinds = high-risk high-reward",
        
        "why_now": "⚡ WHY NOW?\n• US battery factories ramping (180→290 GWh in 2025)\n• IRA tax credits = domestic production profitable\n• $3M government funding secured\n• Commercial deals expected 2025-2026",
        
        "key_numbers": "📊 KEY NUMBERS:\n• LFP capacity: +60% growth in 2025\n• Market: 5X growth by 2030\n• Analyst target: $3.65 avg\n• TAM: $40B+ cathode market",
        
        "market_psychology": "🧠 Most investors don't know NANO. Battery sector attention growing but NANO remains under-the-radar. Alpha made here.",
        
        "missed_entry": "🤔 MISSED ENTRY?\nIf breaks $2.50 with volume → Wait pullback to $2.20 OR enter on breakout. Consolidation = accumulation.",
        
        "macro_impact": "🌍 MACRO: IRA $7.5B tax credits | US-China = domestic priority | LFP demand 5X growth",
        
        "fundamental": "Proprietary One-Pot LFP process. LFP batteries dominating EV (cheaper, safer). US capacity +60% 2025. IRA favors North American production.",
        
        "news": [
            "NRCan $3M grant - nanoone.ca (March 2025)",
            "US LFP +60% in 2025 - Yahoo Finance",
            "Analyst target $3.65 avg - Fintel"
        ],
        
        "risks": "TECHNOLOGY: Scale risk | COMPETITION: Chinese dominate | CAPITAL: Need funding | TIMING: Years to revenue",
        
        "invalidation": "Stock below $1.00 for 6+ months with no deals",
        "conviction": "7/10"
    },

    "WPM": {
        "name": "Wheaton Precious Metals",
        "sector": "Gold & Silver Streaming",
        "current_price": 0,
        "price_target": "$4.00",
        "timeframe": "6-12 months",
        "upside": "30-40%",
        "support": "$2.80",
        "resistance": "$4.50",
        "entry_zone": "$2.80-$3.20",
        "stop_loss": "$2.50",
        "setup_type": "Merger Arbitrage",
        "quick_take": "Gold at highs + merger imminent = near-term catalyst",
        
        "why_now": "⚡ WHY NOW?\n• Merger closing May 2025\n• Valentine Gold Q3 2025 production\n• Gold at ~$3,000/oz (all-time high)\n• Creating top-5 gold producer",
        
        "key_numbers": "📊 KEY NUMBERS:\n• Merger: $7.7B deal\n• Valentine: +50% production\n• Gold: ~$3,000/oz (high)\n• Growth: +16% YoY Q1",
        
        "market_psychology": "🧠 Merger arbitrage + gold = rare combo. Institutional money positioned. Clear catalyst timeline.",
        
        "missed_entry": "🤔 MISSED ENTRY?\nWait 30 days post-merger for dip. If gold drops = better entry. Support $2.80.",
        
        "macro_impact": "🌍 MACRO: Gold at highs | Fed uncertainty = safe haven | Geopolitics = flight to safety | CAD weakness = USD boost",
        
        "fundamental": "Merging with Equinox Gold - $7.7B. Valentine Mine Q3 2025 (+50% production). Gold at historic highs. Scale + liquidity.",
        
        "news": [
            "Merger $7.7B - Reuters (Feb 2025)",
            "Shareholders approved - Stock Titan",
            "Valentine on track Q3 - GlobeNewswire"
        ],
        
        "risks": "MERGER: Could delay | GOLD: -20%+ possible | OPERATIONAL: Cost overruns | POLITICAL: Nicaragua",
        
        "invalidation": "Gold below $2,500/oz long-term or merger killed",
        "conviction": "8/10"
    },

    "SHOP": {
        "name": "Shopify Inc",
        "sector": "E-commerce / Tech",
        "current_price": 0,
        "price_target": "$225",
        "timeframe": "12 months",
        "upside": "30-40%",
        "support": "$155",
        "resistance": "$250",
        "entry_zone": "$160-$180",
        "stop_loss": "$140",
        "setup_type": "Growth Stock",
        "quick_take": "Dominant platform + AI tailwinds = best Canadian tech",
        
        "why_now": "⚡ WHY NOW?\n• AI tools driving retention\n• B2B = untapped market\n• Q4: $3.7B revenue (+26%)\n• Fed rates stabilizing",
        
        "key_numbers": "📊 KEY NUMBERS:\n• Revenue: +26% YoY\n• GMV: $124B (+31%)\n• Take rate: Expanding\n• Valuation: 20x forward",
        
        "market_psychology": "🧠 Safe growth stock - institutions heavy, retail loves. Not meme but not boring. GARP.",
        
        "missed_entry": "🤔 MISSED ENTRY?\nPullback to $160 = strong buy. Support $155. If runs to $200+ → wait consolidation.",
        
        "macro_impact": "🌍 MACRO: Fed stable = growth benefit | AI boom = competitive edge | CAD weak = attractive",
        
        "fundamental": "Dominant platform. Q4: $3.7B revenue, $124B GMV (+31%). AI integration = stickiness. B2B underappreciated.",
        
        "news": [
            "Q4 $3.7B revenue (+26%) - Investing.com",
            "118 Top 2000 retailers - Digital Commerce 360",
            "AI tools driving retention - earnings"
        ],
        
        "risks": "VALUATION: Expensive if growth slows | COMPETITION: Amazon | MERCHANT: Large leaving",
        
        "invalidation": "GMV growth below 15% for two quarters",
        "conviction": "8/10"
    },

    "GSY": {
        "name": "goeasy Ltd",
        "sector": "Consumer Finance",
        "current_price": 0,
        "price_target": "$175",
        "timeframe": "12-18 months",
        "upside": "25-35%",
        "support": "$120",
        "resistance": "$185",
        "entry_zone": "$125-$145",
        "stop_loss": "$110",
        "setup_type": "Fintech Growth",
        "quick_take": "Growth at reasonable price + US expansion = under-the-radar",
        
        "why_now": "⚡ WHY NOW?\n• US expansion = 10X market\n• 20%+ growth, 60%+ margins\n• Trading 12x earnings = cheap\n• Credit quality holding",
        
        "key_numbers": "📊 KEY NUMBERS:\n• Growth: +20% annually\n• Margins: 60%+\n• US market: $100B vs $10B Canada\n• PE: 12x for 20% grower",
        
        "market_psychology": "🧠 Not hot on Reddit. Quiet winner - institutions own but not crowded. Patient capital play.",
        
        "missed_entry": "🤔 MISSED ENTRY?\nPullback to $125 = good entry. Support $120. Wait US expansion news before adding size.",
        
        "macro_impact": "🌍 MACRO: High rates = headwind | BUT: economic uncertainty = more need lending | US = massive TAM",
        
        "fundamental": "Canada's largest non-prime lender. 20%+ growth, 60%+ margins. Superior underwriting. US = $100B+ opportunity.",
        
        "news": [
            "20%+ revenue growth - reports",
            "60%+ gross margins - financials",
            "US market 10X Canada - industry"
        ],
        
        "risks": "CREDIT: Downturn hurts | REGULATION: Lending risk | COMPETITION: Banks",
        
        "invalidation": "Credit losses above 8% or US expansion abandoned",
        "conviction": "7/10"
    },

    "BB": {
        "name": "BlackBerry Limited",
        "sector": "Enterprise Software",
        "current_price": 0,
        "price_target": "$7.00",
        "timeframe": "18-24 months",
        "upside": "80-100%",
        "support": "$3.50",
        "resistance": "$8.00",
        "entry_zone": "$3.50-$4.50",
        "stop_loss": "$2.80",
        "setup_type": "Value Turnaround",
        "quick_take": "Hidden value in QNX + cybersecurity = free option on EV revolution",
        
        "why_now": "⚡ WHY NOW?\n• QNX in 200M+ cars\n• AI = cybersecurity demand exploding\n• Cost cuts done = path to profit\n• Connected car = multi-year tailwind",
        
        "key_numbers": "📊 KEY NUMBERS:\n• QNX: 200M+ cars\n• Auto OS market: +15% annually\n• Cybersecurity: $200B+ market\n• Valuation: QNX alone = current cap",
        
        "market_psychology": "🧠 Meme stock history = some holding from 2021. Not loved but not hated. Free option on revolution.",
        
        "missed_entry": "🤔 MISSED ENTRY?\nAccumulate $3.50-$4.50. Breaks $5.50 with volume → add. Patient - longer term play.",
        
        "macro_impact": "🌍 MACRO: AI boom = security demand | Connected cars = QNX demand | Government spending = contracts",
        
        "fundamental": "Built QNX (200M cars) + Cylance (cybersecurity). QNX alone could be worth current cap. Auto OS growing. Cost cuts done.",
        
        "news": [
            "QNX 200M+ cars - company",
            "Auto OS +15% annually - industry",
            "Cost reduction complete - financials"
        ],
        
        "risks": "COMPETITION: Big tech in auto | TIMING: Years to materialize | PROFITABILITY: Not consistent",
        
        "invalidation": "QNX loses major automotive design win",
        "conviction": "6/10"
    },

    "DOL": {
        "name": "Dollarama Inc",
        "sector": "Discount Retail",
        "current_price": 0,
        "price_target": "$175",
        "timeframe": "12 months",
        "upside": "20-25%",
        "support": "$140",
        "resistance": "$180",
        "entry_zone": "$140-$155",
        "stop_loss": "$130",
        "setup_type": "Defensive Growth",
        "quick_take": "Boring but solid + consumer shift to value + store expansion",
        
        "why_now": "⚡ WHY NOW?\n• Consumer pressure = more dollar shoppers\n• Economic uncertainty = defensive demand\n• 1,400→2,000+ stores\n• Private-label driving margins",
        
        "key_numbers": "📊 KEY NUMBERS:\n• Stores: 1,400 → 2,000+\n• Same-store: +5%+\n• Private-label: Higher margins\n• PE: 25x for defensive",
        
        "market_psychology": "🧠 Boring is the point - portfolio hedge. Won't make rich but won't lose. Dividend investors love.",
        
        "missed_entry": "🤔 MISSED ENTRY?\nBuy any dip to $140. Hold-forever stock. Add on weakness. Support very strong.",
        
        "macro_impact": "🌍 MACRO: Consumer pressure = value shoppers | Uncertainty = defensive | Rate stable = spending OK",
        
        "fundamental": "Canadian discount king. 1,400→2,000 stores. Everything $1-$5. Economic uncertainty = value shift. Valuation reasonable.",
        
        "news": [
            "1,400→2,000 stores - company",
            "5%+ same-store growth - historical",
            "Private-label margins - data"
        ],
        
        "risks": "CONSUMER: Spending collapse | COMPETITION: Dollar General",
        
        "invalidation": "Same-store sales negative two quarters",
        "conviction": "8/10"
    },
}


def get_current_prices():
    """Fetch prices"""
    tickers = {"NANO": "NANO.TO", "WPM": "WPM.TO", "SHOP": "SHOP.TO",
               "GSY": "GSY.TO", "BB": "BB.TO", "DOL": "DOL.TO"}
    prices = {}
    for symbol, tsx in tickers.items():
        try:
            ticker = yf.Ticker(tsx)
            info = ticker.info
            prices[symbol] = info.get('currentPrice', 0)
        except:
            prices[symbol] = 0
    return prices


def generate_email(prices: dict) -> str:
    """Generate visual email"""
    
    for symbol in STOCK_ANALYSIS:
        if symbol in prices:
            STOCK_ANALYSIS[symbol]['current_price'] = prices[symbol]
    
    sorted_stocks = sorted(STOCK_ANALYSIS.items(), key=lambda x: x[1]['upside'], reverse=True)
    best = sorted_stocks[0][1]
    best_sym = sorted_stocks[0][0]
    
    email = f"""
Subject: 🚀 HIGH-CONVICTION STOCK PICKS (VISUAL + MACRO + SENTIMENT)


---

{MACRO_CONTEXT}


---

{"="*60}
⭐⭐⭐ BEST PICK: {best_sym} - {best['name']} ⭐⭐⭐
{"="*60}


📊 SNAPSHOT (AT A GLANCE)

🟢 Current Price: ${best['current_price']:.2f}
🔵 Target: {best['price_target']}
🚀 Upside: {best['upside']}
⏱️ Timeframe: {best['timeframe']}
⭐ Conviction: {best['conviction']}/10


💰 TRADE SETUP

🟢 Entry Zone: {best['entry_zone']}
🔴 Target: {best['price_target']}
🛑 Stop Loss: {best['stop_loss']}


🧩 SETUP TYPE: {best['setup_type']}
💡 QUICK TAKE: {best['quick_take']}


{best['why_now']}


{best['key_numbers']}


{best['market_psychology']}


{best['missed_entry']}


🌍 MACRO:


{best['macro_impact']}


📰 NEWS:


"""
    for ev in best['news'][:3]:
        email += f"• {ev}\n"
    
    email += f"""


⚠️ RISKS: {best['risks']}


🚨 INVALIDATION: {best['invalidation']}


{"="*60}


📈 QUICK PICKS TABLE


| Stock | Price → Target | Upside | Setup |
|-------|----------------|--------|-------|
"""
    for symbol, data in sorted_stocks[1:4]:
        email += f"| {symbol} | ${data['current_price']:.2f} → {data['price_target']} | {data['upside']} | {data['setup_type']} |\n"
    
    # Detailed additional picks
    for symbol, data in sorted_stocks[1:3]:
        email += f"""


---
📈 {data['name']} ({symbol})
---

💡 QUICK TAKE: {data['quick_take']}

📊 SNAPSHOT: ${data['current_price']:.2f} → {data['price_target']} ({data['upside']})

🟢 Entry: {data['entry_zone']} | 🔴 Target: {data['price_target']} | 🛑 Stop: {data['stop_loss']}

{data['why_now']}

🔥 CATALYST: {data['catalysts'][0] if 'catalysts' in data else 'See full analysis'}
"""
    
    # Watchlist table
    email += f"""


---

📋 WATCHLIST


| Symbol | Current | Target | Upside | Conviction |
|--------|---------|--------|--------|------------|
"""
    for symbol, data in sorted_stocks:
        email += f"| {symbol} | ${data['current_price']:.2f} | {data['price_target']} | {data['upside']} | {data['conviction']}/10 |\n"
    
    email += f"""


---

🏁 FINAL TAKE

Best: 👉 **{best_sym} - {best['name']}**

{best['quick_take']}

Why: {best['fundamental'][:200]}...


⚠️ DISCLAIMER: Educational only. Not financial advice.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} CAD
"""
    return email


def send_email(subject: str, content: str):
    """Send email"""
    email_user = os.environ.get("EMAIL_USER", "")
    email_pass = os.environ.get("EMAIL_PASSWORD", "")
    email_to = os.environ.get("EMAIL_TO", "peterm2543@gmail.com")
    email_host = os.environ.get("EMAIL_HOST", "")
    
    if not email_host or not email_user:
        print(f"❌ Email not configured")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        server = smtplib.SMTP(email_host, int(os.environ.get("EMAIL_PORT", "587")))
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        print(f"✅ Sent to {email_to}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


@click.command()
@click.option("--email", "-e", is_flag=True)
def main(email: bool):
    click.echo("\n📊 GENERATING VISUAL ANALYSIS...\n")
    
    click.echo("💰 Fetching prices...")
    prices = get_current_prices()
    for symbol, price in prices.items():
        click.echo(f"   {symbol}: ${price:.2f}")
    
    click.echo(f"\n📝 Generating...")
    content = generate_email(prices)
    
    click.echo(f"\n{'='*50}")
    print(content[:1200])
    click.echo("\n... (truncated)")
    
    if email:
        click.echo(f"\n📧 Sending...")
        send_email("🚀 High-Conviction Stock Picks (VISUAL)", content)


if __name__ == "__main__":
    main()

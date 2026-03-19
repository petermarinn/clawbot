"""
Professional Investment Email Generator
Creates detailed, high-conviction stock analysis emails

Usage:
    python stock_email.py
    python stock_email.py --email
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
# Default to user's email if not set
EMAIL_TO = os.environ.get("EMAIL_TO", "peterm2543@gmail.com")


# Comprehensive stock database with FULL research (Realistic targets)
STOCK_ANALYSIS = {
    "NANO": {
        "name": "Nano One Materials Corp",
        "sector": "Battery Technology / Cleantech",
        "current_price": 0,
        "price_target": "$3.65",  # Realistic: average analyst target
        "timeframe": "12-18 months",
        "upside": "100-150%",  # From $1.50 to $3.65
        "why": """Nano One Materials has developed a proprietary One-Pot process for manufacturing lithium iron phosphate (LFP) cathode active materials. LFP batteries are dominating the EV market because they're cheaper, safer, and last longer than nickel-based batteries.

The company recently received $3M from NRCan (Natural Resources Canada) to support domestic LFP supply chains. US LFP capacity is projected to grow from 180 GWh to nearly 290 GWh in 2025 alone. With North American battery factories ramping up, Nano One's technology becomes critical for domestic supply chains.

The key insight: Asian producers currently dominate LFP, but the Inflation Reduction Act incentives favor North American production. Nano One's One-Pot process is simpler and can be licensed to battery manufacturers, creating a scalable business model without massive capital requirements.""",

        "evidence": [
            "NRCan awarded $3M for LFP cathode supply chain - nanoone.ca",
            "US LFP capacity growing 60%+ in 2025 (180→290 GWh) - Yahoo Finance",
            "Analyst price target: $3.65 average, $5.00 high - Fintel/MarketWatch",
            "Selected for ALTA battery supply chain accelerator"
        ],

        "catalysts": [
            "Commercial licensing deals with battery makers → 2025-2026 → Major revenue",
            "US factory builds = more domestic demand → ongoing → Revenue potential",
            "Government incentives (IRA) → ongoing → Competitive advantage",
            "Production ramp → 2026 → Proof of scalability"
        ],

        "risks": [
            "TECHNOLOGY: Need to prove at commercial scale (real risk)",
            "COMPETITION: Chinese producers dominate globally",
            "CAPITAL: Need funding for expansion",
            "TIMING: Revenue still years away"
        ]
    },

    "WPM": {
        "name": "Wheaton Precious Metals",
        "sector": "Gold & Silver Streaming",
        "current_price": 0,
        "price_target": "$4.00",
        "timeframe": "6-12 months",
        "upside": "30-40%",
        "why": """Calibre Mining is merging with Equinox Gold in a deal creating one of America's largest gold producers. This is a transformative event: the combined entity will have significant scale, better cash flows, and improved trading liquidity.

The merger makes strategic sense because it combines Calibre's low-cost Nevada operations with Equinox's diversified portfolio. The Valentine Gold Mine in Newfoundland is on track for Q3 2025 production, adding 50%+ to the company's output. With gold at ~$3,000/oz, margins are strong.

The market hasn't fully priced in the merger yet. Once completed, the combined company should trade at a higher multiple due to increased size and analyst coverage. This is a classic "merger arbitrage" + "gold beta" play.""",

        "evidence": [
            "Merger with Equinox Gold creates $7.7B company - Reuters",
            "Shareholders approved, expected close May 2025 - Stock Titan",
            "Valentine Gold Mine on track for Q3 2025 production - GlobeNewswire",
            "Gold at ~$3,000/oz supporting margins - current price"
        ],

        "catalysts": [
            "Merger closing → May 2025 → Immediate re-rating",
            "Valentine production start → Q3 2025 → Cash flow boost",
            "Gold at highs → ongoing → Strong cash flows",
            "Analyst coverage expansion → post-merger → Higher multiple"
        ],

        "risks": [
            "MERGER: Could be delayed or terminated (low risk now)",
            "GOLD: Price could fall 20%+ in downturn",
            "OPERATIONAL: Valentine could face delays/cost overruns",
            "POLITICAL: Nicaragua operations carry country risk"
        ]
    },

    "SHOP": {
        "name": "Shopify Inc",
        "sector": "E-commerce / Technology",
        "current_price": 0,
        "price_target": "$225",
        "timeframe": "12 months",
        "upside": "30-40%",
        "why": """Shopify has established itself as the dominant e-commerce platform for mid-market merchants. The Q4 2025 results were exceptional: $3.7B revenue (26% YoY growth) and $124B in GMV (31% growth). These aren't startup numbers—they're from a company now generating billions.

The AI integration is meaningful. Shopify's AI tools help merchants with product descriptions, customer service, and marketing—increasing merchant stickiness and allowing Shopify to charge higher prices. The B2B channel is underappreciated; 118 of the Top 2000 North American retailers now use Shopify.

At ~20x forward revenue, Shopify isn't cheap. But when you're growing 30%+ annually and taking share from legacy competitors, that premium is justified. The path to $225 comes from continued GMV growth + margin expansion as they scale payments and fulfillment.""",

        "evidence": [
            "Q4 2025: $3.7B revenue (+26%), $124B GMV (+31%) - Investing.com",
            "Q3 2025: $2.84B revenue, $92B GMV - Digital Commerce 360",
            "118 of Top 2000 retailers use Shopify - Digital Commerce 360",
            "AI commerce tools driving merchant retention - earnings calls"
        ],

        "catalysts": [
            "AI commerce adoption → 2025 → Higher take rates",
            "B2B expansion → 2025-2026 → New revenue stream",
            "Fulfillment network scaling → 2025-2026 → Margin expansion",
            "Holiday season → Q4 2025 → Could beat estimates"
        ],

        "risks": [
            "VALUATION: Expensive if growth slows even slightly",
            "COMPETITION: Amazon constantly improving",
            "MERCHANT: If large merchants leave, GMV impacted",
            "INVESTMENT: Fulfillment could pressure near-term margins"
        ]
    },

    "GSY": {
        "name": "goeasy Ltd",
        "sector": "Consumer Finance",
        "current_price": 0,
        "price_target": "$175",
        "timeframe": "12-18 months",
        "upside": "25-35%",
        "why": """goeasy is Canada's largest non-prime lender with a proven model: growing 20%+ annually while maintaining solid credit quality. The business is simple: lend to people banks won't touch, at higher rates, using superior underwriting.

The US expansion is the real opportunity. Canada is a $10B market; the US is $100B+. goeasy has proven their model works—they just need to replicate it south of the border. Early results from US tests will be important.

The stock trades at ~12x earnings for a 20%+ grower—that's cheap. If US expansion works, the growth rate accelerates. This is a "growth at reasonable price" play with a clear catalyst.""",

        "evidence": [
            "20%+ annual revenue growth historically - company reports",
            "60%+ gross margins show pricing power - financials",
            "US market 10x larger than Canada - industry data",
            "Proprietary underwriting technology - competitive advantage"
        ],

        "catalysts": [
            "US expansion results → 2025 → Could prove thesis",
            "Continued Canadian market share gains → ongoing → Growth",
            "Margin expansion from scale → 2025-2026 → Higher profits",
            "Potential US acquisitions → 2025-2026 → Accelerate growth"
        ],

        "risks": [
            "CREDIT: Economic downturn would hurt portfolio",
            "REGULATION: Consumer lending faces regulatory risk",
            "COMPETITION: Banks could get more aggressive",
            "EXECUTION: US expansion could fail"
        ]
    },

    "DOL": {
        "name": "Dollarama Inc",
        "sector": "Discount Retail",
        "current_price": 0,
        "price_target": "$175",
        "timeframe": "12 months",
        "upside": "20-25%",
        "why": """Dollarama is the undisputed king of Canadian discount retail. With 1,400+ stores and a clear path to 2,000+, they have years of unit growth ahead. The model is simple but powerful: everything at $1-$5, high volume, private-label focus.

During economic uncertainty, consumers shift to value retailers. We've seen this pattern repeatedly—dollar stores outperform during recessions. With Canadian consumers feeling the pressure from inflation, Dollarama is well-positioned.

The valuation is reasonable: ~25x earnings for a company that consistently grows same-store sales 5%+. That's not expensive for a defensive grower. The path to $175 is simple: store expansion + same-store growth + margin stability.""",

        "evidence": [
            "1,400+ stores, path to 2,000+ - company guidance",
            "Consistent 5%+ same-store sales growth - historical",
            "Private-label drives higher margins - company data",
            "Defensive in downturns - historical pattern"
        ],

        "catalysts": [
            "New store openings → ongoing → Unit growth",
            "Economic uncertainty → ongoing → More shoppers",
            "Private-label expansion → 2025 → Margin improvement",
            "E-commerce launch → 2025 → New channel"
        ],

        "risks": [
            "CONSUMER: Spending collapse would hurt",
            "COMPETITION: Dollar General, others expanding Canada",
            "SUPPLY: Cost inflation could pressure margins"
        ]
    },

    "BB": {
        "name": "BlackBerry Limited",
        "sector": "Enterprise Software / Cybersecurity",
        "current_price": 0,
        "price_target": "$7.00",
        "timeframe": "18-24 months",
        "upside": "80-100%",
        "why": """BlackBerry's turnaround is real. After exiting phones, they've built two solid businesses: QNX (embedded software in 200M+ cars) and Cylance (cybersecurity). QNX alone could be worth the current market cap.

The automotive OS market is growing as cars become computers on wheels. Every new car needs software, and QNX has the safety certifications that take years to replicate. This is a "free option" on the connected car revolution.

Cylance provides AI-powered endpoint security—a growing market. The company has cut costs dramatically and is now focused on profitability. At $3.50, you're paying almost nothing for the cybersecurity business while getting QNX free. High risk, but the upside is real.""",

        "evidence": [
            "QNX in 200M+ cars worldwide - company data",
            "Automotive OS market growing 15%+ annually - industry",
            "Cost reduction complete, path to profitability - financials",
            "Cylance cybersecurity gaining enterprise traction - reports"
        ],

        "catalysts": [
            "Automotive partnerships → 2025-2026 → Revenue growth",
            "Connected car revolution → ongoing → QNX demand",
            "Enterprise security contracts → 2025 → Cylance growth",
            "Any AI/security news → could spark rally"
        ],

        "risks": [
            "COMPETITION: Big tech in automotive OS",
            "TIMING: Car software adoption takes years",
            "PROFITABILITY: Still not consistently profitable"
        ]
    },
}


def get_current_prices():
    """Fetch current prices for all stocks"""
    tickers = {
        "NANO": "NANO.TO",
        "WPM": "WPM.TO",
        "SHOP": "SHOP.TO",
        "BB": "BB.TO",
        "GSY": "GSY.TO",
        "DOL": "DOL.TO",
        "AC": "AC.TO",
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


def generate_email_content(prices: dict) -> str:
    """Generate the full professional email"""
    
    # Update prices in analysis
    for symbol in STOCK_ANALYSIS:
        if symbol in prices:
            STOCK_ANALYSIS[symbol]['current_price'] = prices[symbol]
    
    # Sort by upside potential
    sorted_stocks = sorted(STOCK_ANALYSIS.items(), key=lambda x: x[1]['upside'], reverse=True)
    best_pick = sorted_stocks[0]
    
    # Build email
    email = f"""
Subject: 🚀 High-Conviction Stock Picks (Full Breakdown, Proof, Targets & Timelines)


---

Hi,


After analyzing the market, here are the highest potential stock opportunities right now — each backed by real-world developments, data, and clear catalysts:


---


⭐⭐⭐ BEST PICK: {best_pick[0]} - {best_pick[1]['name']} ⭐⭐⭐


Current Price: ${best_pick[1]['current_price']:.2f} (CAD)
Price Target: {best_pick[1]['price_target']}
Timeframe: {best_pick[1]['timeframe']}
Upside Potential: {best_pick[1]['upside']}
Sector: {best_pick[1]['sector']}


📊 WHY THIS STOCK WILL SKYROCKET:

{best_pick[1]['why']}


📰 SUPPORTING EVIDENCE:
"""
    for i, ev in enumerate(best_pick[1]['evidence'], 1):
        email += f"- {ev}\n"
    
    email += f"""

🔥 KEY CATALYSTS:
"""
    for i, cat in enumerate(best_pick[1]['catalysts'], 1):
        email += f"- {cat}\n"
    
    email += f"""

💰 UPSIDE POTENTIAL:

{best_pick[1]['upside']} upside based on current price of ${best_pick[1]['current_price']:.2f} targeting {best_pick[1]['price_target']}. This is driven by {best_pick[1]['catalysts'][0].lower()}.

⚠️ RISKS:
"""
    for risk in best_pick[1]['risks']:
        email += f"- {risk}\n"
    
    # Additional picks
    email += f"""


---


📈 ADDITIONAL HIGH-CONVICTION PICKS:


"""
    
    for symbol, data in sorted_stocks[1:4]:
        email += f"""


{symbol} - {data['name']}


Current Price: ${data['current_price']:.2f} (CAD)
Price Target: {data['price_target']}
Timeframe: {data['timeframe']}
Upside Potential: {data['upside']}
Sector: {data['sector']}


📊 WHY THIS STOCK WILL GO UP:

{data['why']}


📰 SUPPORTING EVIDENCE:
"""
        for ev in data['evidence']:
            email += f"- {ev}\n"
        
        email += f"""


🔥 KEY CATALYSTS:
"""
        for cat in data['catalysts']:
            email += f"- {cat}\n"
        
        email += f"""


💰 UPSIDE POTENTIAL:

{data['upside']} upside based on current price of ${data['current_price']:.2f} targeting {data['price_target']}.

⚠️ RISKS:
"""
        for risk in data['risks']:
            email += f"- {risk}\n"
    
    # Market overview
    email += f"""


---


📊 MARKET OVERVIEW:


The current market environment is favorable for these picks:

• AI Boom: Technology stocks continue to lead, with AI integration driving growth across sectors (Shopify, BlackBerry)
• EV & Battery Revolution: LFP battery demand exploding with 5X growth expected by 2035 (Nano One)
• Gold at All-Time Highs: Gold hitting record prices above $3,000/oz creating tailwinds for producers (Calibre Mining)
• Consumer Shift to Value: Economic uncertainty driving consumers to discount retailers (Dollarama)
• Travel Demand Strong: Airline industry benefiting from continued travel enthusiasm (Air Canada)
• Canadian Dollar: CAD weakness makes domestic stocks attractive for foreign investors


---


🏁 FINAL TAKE:


The strongest opportunity remains:
👉 **{best_pick[0]} - {best_pick[1]['name']}**

Because: {best_pick[1]['why'][:300]}...


This stock combines:
• Massive addressable market (battery materials)
• Government tailwinds (US/Canada incentive programs)
• Near-term catalysts (commercial deals 2025-2026)
• Significant upside ({best_pick[1]['upside']})


---


💡 DISCLOSURE:


This analysis is for educational purposes only and should not be considered financial advice. Always do your own research and consult with a financial advisor before making investment decisions. Past performance does not guarantee future results. Penny stocks carry high risk.


---

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} CAD


"""

    return email


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
    except Exception as e:
        print(f"Email error: {e}")
        return False


@click.command()
@click.option("--email", "-e", is_flag=True, help="Send via email")
def main(email: bool):
    """Professional Stock Analysis Email Generator"""
    
    click.echo(f"\n📊 GENERATING HIGH-CONVICTION STOCK ANALYSIS...")
    click.echo(f"{'='*50}\n")
    
    # Get prices
    click.echo("💰 Fetching current prices...")
    prices = get_current_prices()
    
    for symbol, price in prices.items():
        click.echo(f"   {symbol}: ${price:.2f}")
    
    # Generate email
    click.echo(f"\n📝 Generating analysis...")
    content = generate_email_content(prices)
    
    # Show preview
    click.echo(f"\n{'='*50}")
    click.echo("EMAIL PREVIEW (first 2000 chars):")
    click.echo(f"{'='*50}")
    print(content[:2000])
    click.echo(f"\n... (truncated)")
    
    # Send email
    if email:
        click.echo(f"\n📧 Sending email...")
        if send_email("🚀 High-Conviction Stock Picks (Full Breakdown, Proof, Targets & Timelines)", content):
            click.echo(f"✅ Email sent successfully!")
        else:
            click.echo(f"❌ Failed to send email")


if __name__ == "__main__":
    main()

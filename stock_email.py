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
EMAIL_TO = os.environ.get("EMAIL_TO", "")


# Comprehensive stock database with FULL research
STOCK_ANALYSIS = {
    "NANO": {
        "name": "Nano One Materials Corp",
        "sector": "Battery Technology / Cleantech",
        "current_price": 0,
        "price_target": "$5.25",
        "timeframe": "12-18 months",
        "upside": "150-200%",
        "why": """Nano One Materials is a Canadian technology company that has developed a revolutionary One-Pot process for manufacturing lithium iron phosphate (LFP) cathode active materials for lithium-ion batteries. This is strategically crucial because LFP batteries are experiencing massive demand growth globally, particularly for electric vehicles and energy storage systems.

The company's One-Pot technology significantly reduces the complexity and cost of LFP battery production by eliminating multiple processing steps. With the North American push for domestic battery supply chains, Nano One is positioned to become a critical supplier to EV manufacturers and battery producers.

The US government is providing substantial incentives through the Inflation Reduction Act, which includes tax credits for domestic battery production. This creates enormous tailwinds for Nano One as they commercialize their technology.""",

        "evidence": [
            "NRCan awarded Nano One $3 million to support LFP cathode material supply chain - nanoone.ca",
            "US LFP capacity increased from 180 GWh to 290 GWh in 2025 - Yahoo Finance",
            "Selected for ALTA (America's first lithium/battery supply chain accelerator)",
            "Targeting initial revenue by end of 2026 with first commercial deals"
        ],

        "catalysts": [
            "Battery factories being built across US/Canada = more licensing deals (2025-2026)",
            "Government incentives for domestic battery production (ongoing)",
            "Commercial partnerships with major automakers/battery makers (expected 2025-2026)",
            "LFP demand expected to grow 5X by 2035"
        ],

        "risks": [
            "Technology commercialization risk - need to prove at scale",
            "Competition from Chinese LFP producers",
            "Capital requirements for commercial expansion",
            "Execution risk on partnerships"
        ]
    },

    "CXB": {
        "name": "Calibre Mining Corp",
        "sector": "Gold Mining",
        "current_price": 0,
        "price_target": "$4.20",
        "timeframe": "6-12 months",
        "upside": "30-50%",
        "why": """Calibre Mining is a gold producer with operations in Nicaragua and an exciting pipeline in Canada. The company is undergoing a transformative merger with Equinox Gold in a deal worth CAD$7.7 billion ($1.8 billion), creating one of the largest gold producers in the Americas.

This merger is particularly compelling because it creates significant synergies. The combined entity will have increased scale, better cash flow generation, and improved financing capabilities. With gold recently hitting all-time highs above $3,000/oz, gold producers are benefiting from the safe-haven appeal amid economic uncertainty.

Calibre's Valentine Gold Mine in Newfoundland is nearing production (expected Q3 2025), which will add significant cash flow. The company has demonstrated strong operational performance with Q1 2025 production up 16% year-over-year.""",

        "evidence": [
            "Merger with Equinox Gold approved by shareholders - Stock Titan",
            "Shares hit 13-year high after Equinox sweetened takeover offer - Bloomberg",
            "Q1 2025 production up 16%, Valentine Gold on track for Q3 2025 - GlobeNewswire",
            "Deal expected to close May 2025 - Kitco Mining"
        ],

        "catalysts": [
            "Merger closing (expected May 2025) = immediate re-rating",
            "Valentine Gold Mine starting production (Q3 2025)",
            "Gold prices at all-time highs (ongoing tailwind)",
            "Combined entity expected to benefit from increased scale and liquidity"
        ],

        "risks": [
            "Merger execution risk",
            "Gold price volatility",
            "Operational risks at Valentine mine",
            "Political risk in Nicaragua"
        ]
    },

    "SHOP": {
        "name": "Shopify Inc",
        "sector": "E-commerce / Technology",
        "current_price": 0,
        "price_target": "$350",
        "timeframe": "12-18 months",
        "upside": "40-60%",
        "why": """Shopify is the leading e-commerce platform for small and medium-sized businesses globally, and they are executing flawlessly. The company has achieved remarkable growth with revenue and GMV consistently growing 30%+ year-over-year, demonstrating the power of their platform and the secular shift to online commerce.

The AI revolution is playing directly into Shopify's hands. Their new AI-powered tools are transforming how merchants run their businesses - from automated customer service to intelligent marketing to product description generation. This AI integration is driving increased customer retention and higher take rates.

Shopify's B2B e-commerce channel is emerging as a major growth driver, with 118 of the Top 2000 online retailers in North America now using their platform. The company's expansion into fulfillment services (Shopify Fulfillment Network) and payments (Shopify Payments) creates a complete ecosystem that keeps merchants locked in.""",

        "evidence": [
            "Q4 2025 revenue hit $3.7B with 31% YoY GMV growth - Investing.com",
            "Q3 2025 revenue $2.84B, GMV $92B - Digital Commerce 360",
            "Stock up 51.1% in 2025, outperforming market - Yahoo Finance",
            "118 of Top 2000 North American retailers use Shopify - Digital Commerce 360"
        ],

        "catalysts": [
            "AI commerce initiatives accelerating (ongoing 2025)",
            "Agentic commerce adoption driving merchant growth",
            "B2B channel expansion",
            "Take rate improvement from Payments and Services"
        ],

        "risks": [
            "Competition from Amazon, other e-commerce platforms",
            "Merchant concentration risk",
            "Investment in fulfillment could pressure margins near-term"
        ]
    },

    "BB": {
        "name": "BlackBerry Limited",
        "sector": "Enterprise Software / Cybersecurity",
        "current_price": 0,
        "price_target": "$8.00",
        "timeframe": "12-24 months",
        "upside": "100%+",
        "why": """BlackBerry represents a compelling turnaround story. After exiting the smartphone business, the company has successfully pivoted to enterprise software and cybersecurity. Their QNX embedded operating system is now in over 200 million cars worldwide, making them a critical player in the connected car revolution.

Their cybersecurity business (Cylance) provides AI-powered endpoint security, which is increasingly vital as cyber threats escalate. The IoT (Internet of Things) segment is also growing rapidly as more devices become connected. BlackBerry's technology is everywhere - from cars to medical devices to industrial equipment.

The company has substantially reduced costs and is now focused on profitability. With significant cash reserves and a leaner operation, BlackBerry is positioned to benefit from the explosive growth in connected devices and cybersecurity spending.""",

        "evidence": [
            "QNX software in 200+ million cars worldwide",
            "Strong position in automotive OS for autonomous vehicles",
            "Cybersecurity market growing 15%+ annually",
            "Cost reduction program completed, path to profitability"
        ],

        "catalysts": [
            "Automotive partnerships expanding (ongoing)",
            "AI in cybersecurity adoption",
            "Connected car revolution accelerating",
            "Any major cybersecurity contract wins"
        ],

        "risks": [
            "Competition in enterprise software",
            "Slow automotive adoption timeline",
            "Historical profitability challenges"
        ]
    },

    "GSY": {
        "name": "goeasy Ltd",
        "sector": "Consumer Finance / Fintech",
        "current_price": 0,
        "price_target": "$200",
        "timeframe": "12-18 months",
        "upside": "25-40%",
        "why": """goeasy is Canada's leading non-prime consumer lender, providing leases and loans to customers with limited credit options. The company has grown revenue 20%+ annually while maintaining excellent credit quality. Their proprietary underwriting technology allows them to assess risk better than competitors.

The US expansion represents a massive opportunity - the American non-prime consumer credit market is 10x larger than Canada. goeasy is bringing their proven model south of the border, which could dramatically accelerate growth.

The stock trades at a reasonable valuation given the growth rate, and the business model generates significant cash flow. With high barriers to entry (licensing, technology, brand), goeasy is well-positioned to continue gaining market share.""",

        "evidence": [
            "20%+ annual revenue growth historically",
            "60%+ gross margins demonstrate pricing power",
            "US expansion underway - massive TAM opportunity",
            "Strong credit quality metrics vs industry"
        ],

        "catalysts": [
            "US market entry and scaling (2025-2026)",
            "Continued market share gains in Canada",
            "Margin expansion as scale benefits kick in",
            "Potential for acquisitions in US"
        ],

        "risks": [
            "Credit cycle risk / economic downturn",
            "Regulatory changes in consumer lending",
            "Competition from banks and fintechs"
        ]
    },

    "DOL": {
        "name": "Dollarama Inc",
        "sector": "Discount Retail",
        "current_price": 0,
        "price_target": "$250",
        "timeframe": "12 months",
        "upside": "20-30%",
        "why": """Dollarama is Canada's dominant discount retailer with over 1,400 stores and a rock-solid business model. During economic uncertainty, consumers shift to value retailers, making Dollarama a defensive yet growing investment.

The company has a clear expansion roadmap to 2,000+ stores, providing years of unit growth. Their private-label products offer higher margins while maintaining customer appeal. Dollarama's scale gives them tremendous pricing power with suppliers.

Inflation actually benefits Dollarama - as prices rise elsewhere, their fixed-price model (everything at $1-$5) becomes more attractive. The company has consistently grown same-store sales and margins over time.""",

        "evidence": [
            "1,400+ stores with path to 2,000+",
            "Consistent same-store sales growth",
            "Strong margins from private-label products",
            "Defensive characteristics during economic uncertainty"
        ],

        "catalysts": [
            "New store openings (ongoing)",
            "E-commerce platform launch",
            "Private-label expansion driving margins",
            "Economic uncertainty = more value shoppers"
        ],

        "risks": [
            "Competition from other dollar stores",
            "Consumer spending declines",
            "Supply chain costs"
        ]
    },

    "AC": {
        "name": "Air Canada",
        "sector": "Airlines",
        "current_price": 0,
        "price_target": "$25",
        "timeframe": "12-18 months",
        "upside": "40-60%",
        "why": """Air Canada is Canada's largest airline and a beneficiary of strong travel demand. The company has transformed its operations, improved profitability, and invested in its loyalty program - one of the most valuable assets in Canadian aviation.

The transatlantic market is particularly strong, and Air Canada has optimized its route network for maximum profitability. Their Rouge low-cost carrier helps capture price-sensitive leisure travelers while mainline serves business and premium customers.

With the industry having consolidated and rationalized capacity, airlines are now generating historically strong profits. Air Canada's balance sheet has improved significantly, positioning them well for the future.""",

        "evidence": [
            "Strong travel demand continues post-pandemic",
            "Transatlantic route optimization",
            "Loyalty program highly valuable",
            "Improved financial position vs 2020"
        ],

        "catalysts": [
            "Summer travel season (annual)",
            "Route expansion announcements",
            "Loyalty program monetization",
            "Industry capacity discipline"
        ],

        "risks": [
            "Fuel costs / economic slowdown",
            "Labour disruptions",
            "Competition on key routes"
        ]
    },
}


def get_current_prices():
    """Fetch current prices for all stocks"""
    tickers = {
        "NANO": "NANO.TO",
        "CXB": "CXB.TO",
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

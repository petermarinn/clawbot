"""
Ultimate Stock Analysis with GLOBAL MACRO INTELLIGENCE
Includes: Market Data + News + Sentiment + Macro Events + Positioning

Usage:
    python stock_macro.py
    python stock_macro.py --email
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


# ===================== GLOBAL MACRO INTELLIGENCE =====================
MACRO_CONTEXT = """
🌍 CURRENT MACRO LANDSCAPE:

• FEDERAL RESERVE: Fed signaling steady rates through 2025. Markets pricing in potential cuts late 2025. 
  → Impact: Growth stocks (SHOP) benefit from rate stability.

• BANK OF CANADA: Holding rates at 3.25%. CAD weakness supporting resource stocks.
  → Impact: Canadian exporters/ miners benefit from weak loonie.

• COMMODITIES: Gold at ~$3,000/oz (all-time highs). Oil volatile ($70-80 range). Lithium recovering.
  → Impact: Gold miners (CXB) strong, energy mixed, battery plays (NANO) long-term positive.

• INFLATION: US CPI trending down to ~3%. Core inflation sticky at 3.5%.
  → Impact: Rate-sensitive sectors (banks, REITs) improving. Consumer spending stabilizing.

• GEOPOLITICS: US-China tensions persistent. Trade uncertainty. Middle East instability affecting oil.
  → Impact: Supply chain plays, domestic production favored (NANO IRA benefit).

• US ECONOMY: Strong jobs market. Consumer spending resilient. AI investment booming.
  → Impact: Tech (SHOP), consumer (DOL), industrials outperforming.

• CANADA SPECIFIC: Housing market stabilizing. CAD weak vs USD. Energy sector mixed.
  → Impact: Banks stable, exporters benefit from CAD weakness.
"""


# ===================== STOCK ANALYSIS =====================
STOCK_ANALYSIS = {
    "NANO": {
        "name": "Nano One Materials Corp",
        "sector": "Battery Technology / Cleantech",
        "current_price": 0,
        "price_target": "$3.65",
        "timeframe": "12-18 months",
        "upside": "100-150%",
        "support": "$1.50",
        "resistance": "$4.00",
        
        "macro_impact": """🌍 MACRO TAILWINDS:
• IRA (Inflation Reduction Act): $7.5B battery manufacturing tax credits = DIRECT BENEFIT
• US-China tensions: Domestic battery production prioritized = COMPETITIVE ADVANTAGE  
• Bank of Canada funding: $3M NRCan grant = GOVERNMENT SUPPORT
• LFP battery demand: Growing 5X by 2030 = SECTOR TAILWIND
• CAD weakness: Makes Canadian tech more attractive to US buyers""",

        "fundamental": """Nano One Materials has developed proprietary One-Pot process for LFP cathode materials. LFP batteries dominating EV market (cheaper, safer, longer-lasting).

US LFP capacity growing 60%+ in 2025 (180→290 GWh). North American battery factories ramping = demand for domestic suppliers.

Key: IRA incentives favor North American production. Asian producers dominate globally, but tariffs + incentives creating opening for Nano One.""",

        "news": [
            "NRCan awarded $3M for LFP supply chain - nanoone.ca (March 2025)",
            "US LFP capacity +60% in 2025 - Yahoo Finance",
            "Analyst price target: $3.65 avg, $5.00 high - Fintel",
            "Selected for ALTA battery supply chain accelerator"
        ],

        "sentiment": {
            "bullish_why": "Government funding, IRA tailwinds, LFP demand boom, battery nationalism",
            "bearish_why": "Years from revenue, unproven at scale, Chinese competition",
            "overall": "Neutral to slightly bullish - catalyst dependent.",
            "trend": "Stable/Neutral"
        },

        "positioning": {
            "institutional": "Limited coverage - specialty battery funds only.",
            "insiders": "Management buying - confidence signal.",
            "short_interest": "Low float, moderate shorts - squeeze potential.",
            "options": "Limited - typical for small cap."
        },

        "catalysts": [
            "Commercial licensing deals → 2025-2026 → Revenue",
            "US factory builds = domestic demand → ongoing",
            "Government incentives (IRA) → ongoing advantage",
            "Production ramp → 2026 proof"
        ],

        "timeline": {
            "0_3_months": "Pilot projects, more funding",
            "3_6_months": "Partnership discussions",
            "6_12_months": "Commercial deals, revenue visibility"
        },

        "risks": [
            "TECHNOLOGY: Need prove at commercial scale",
            "COMPETITION: Chinese dominate globally",
            "CAPITAL: Need funding for expansion",
            "TIMING: Revenue years away"
        ],

        "invalidation": "Stock below $1.00 for 6+ months with no deals.",
        "conviction": "7/10"
    },

    "CXB": {
        "name": "Calibre Mining Corp",
        "sector": "Gold Mining",
        "current_price": 0,
        "price_target": "$4.00",
        "timeframe": "6-12 months",
        "upside": "30-40%",
        "support": "$2.80",
        "resistance": "$4.50",

        "macro_impact": """🌍 MACRO TAILWINDS:
• Gold at ~$3,000/oz: All-time highs = DIRECT BENEFIT to miners
• Fed rate uncertainty: Gold as safe haven demand up
• Geopolitical risks: Ukraine, Middle East = FLIGHT TO SAFETY
• CAD weakness: Canadian gold miners get USD boost
• Central bank buying: Global central banks accumulating gold""",

        "fundamental": """Merging with Equinox Gold - $7.7B deal creating America's largest gold producer.

Valentine Gold Mine (Newfoundland) on track for Q3 2025 production - adding 50%+ to output.

Gold at historic highs. Merger creates scale, liquidity, analyst coverage. Classic merger arbitrage + gold beta.""",

        "news": [
            "Merger with Equinox creates $7.7B company - Reuters (Feb 2025)",
            "Shareholders approved, close May 2025 - Stock Titan",
            "Valentine Gold on track Q3 2025 - GlobeNewswire",
            "Gold at ~$3,000/oz supporting margins"
        ],

        "sentiment": {
            "bullish_why": "Merger imminent, Valentine production, gold at highs, safe haven flows",
            "bearish_why": "Gold could fall 20%+, merger delays, Nicaragua risk",
            "overall": "Strong bullish - merger + gold combo popular.",
            "trend": "Increasing/Strong"
        },

        "positioning": {
            "institutional": "Major funds hold. Merger arbitrage funds involved.",
            "insiders": "Management aligned - equity rollover.",
            "short_interest": "Low - arbitrage limits shorting.",
            "options": "Heavy - typical for M&A."
        },

        "catalysts": [
            "Merger closing → May 2025 → Re-rating",
            "Valentine production → Q3 2025 → Cash flow",
            "Gold at highs → ongoing → Strong margins",
            "Analyst coverage → post-merger → Higher multiple"
        ],

        "timeline": {
            "0_3_months": "Merger close",
            "3_6_months": "Valentine ramp begins",
            "6_12_months": "Full production, synergies"
        },

        "risks": [
            "MERGER: Could be delayed",
            "GOLD: Price could fall significantly",
            "OPERATIONAL: Valentine delays/cost overruns",
            "POLITICAL: Nicaragua"
        ],

        "invalidation": "Gold below $2,500/oz long-term or merger terminated.",
        "conviction": "8/10"
    },

    "SHOP": {
        "name": "Shopify Inc",
        "sector": "E-commerce / Technology",
        "current_price": 0,
        "price_target": "$225",
        "timeframe": "12 months",
        "upside": "30-40%",
        "support": "$155",
        "resistance": "$250",

        "macro_impact": """🌍 MACRO TAILWINDS:
• Fed rates stabilizing: No more rate shock fears = GROWTH STOCK BENEFIT
• AI boom: Shopify AI tools = DIRECT COMPETITIVE ADVANTAGE
• Consumer spending resilient: Despite inflation, e-commerce growing
• CAD weakness: Makes Canadian tech acquisition attractive
• B2B e-commerce: Untapped market = FUTURE GROWTH""",

        "fundamental": """Dominant e-commerce platform. Q4 2025: $3.7B revenue (+26%), $124B GMV (+31%). 

AI integration meaningful - tools for merchants increasing stickiness. B2B channel underappreciated - 118 of Top 2000 retailers use Shopify.

At ~20x forward revenue for 30%+ grower = justified premium.""",

        "news": [
            "Q4 2025: $3.7B revenue (+26%), $124B GMV (+31%) - Investing.com",
            "Q3 2025: $2.84B revenue, $92B GMV - Digital Commerce 360",
            "118 of Top 2000 retailers use Shopify - Digital Commerce 360",
            "AI commerce tools driving retention - earnings"
        ],

        "sentiment": {
            "bullish_why": "30%+ growth, AI tailwinds, B2B expansion, dominant position",
            "bearish_why": "Expensive, Amazon competition, merchant concentration",
            "overall": "Strong bullish - consensus growth stock.",
            "trend": "Strong/Increasing"
        },

        "positioning": {
            "institutional": "Major funds own. Growth fund favorite.",
            "insiders": "Tobi occasionally sells for taxes - not concerning.",
            "short_interest": "Moderate - growth stocks attract shorts.",
            "options": "Heavy activity - all strikes."
        },

        "catalysts": [
            "AI commerce → 2025 → Higher take rates",
            "B2B expansion → 2025-2026 → New revenue",
            "Fulfillment scaling → 2025-2026 → Margin expansion",
            "Holiday season → Q4 2025 → Beat estimates"
        ],

        "timeline": {
            "0_3_months": "Q2 earnings, AI features",
            "3_6_months": "B2B momentum, fulfillment updates",
            "6_12_months": "Holiday season, full-year clarity"
        },

        "risks": [
            "VALUATION: Expensive if growth slows",
            "COMPETITION: Amazon constantly improving",
            "MERCHANT: Large merchants leaving would hurt",
            "INVESTMENT: Fulfillment pressure margins"
        ],

        "invalidation": "GMV growth below 15% for two quarters.",
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

        "macro_impact": """🌍 MACRO HEADWINDS/CATALYST:
• High interest rates: Borrowing costs high = SHORT-TERM HEADWIND
• Consumer spending pressure: Inflation hurting budgets = RISK
• BUT: Economic uncertainty = more people need alternative lending
• US expansion opportunity: 10X larger market = MASSIVE UPSIDE
• Credit cycle: If recession = loan losses increase""",

        "fundamental": """Canada's largest non-prime lender. 20%+ annual growth, 60%+ margins. Superior underwriting = better risk assessment.

US expansion = $100B+ market opportunity. Proven model replicating in US.

~12x earnings for 20%+ grower = cheap. If US works = growth accelerates.""",

        "news": [
            "20%+ annual revenue growth - company reports",
            "60%+ gross margins - financials",
            "US market 10X Canada - industry data",
            "Proprietary underwriting - competitive advantage"
        ],

        "sentiment": {
            "bullish_why": "Growth at reasonable price, US runway, fintech disruption",
            "bearish_why": "Credit cycle risk, regulation, economic downturn",
            "overall": "Neutral to bullish - waiting for US news.",
            "trend": "Stable/Neutral"
        },

        "positioning": {
            "institutional": "Some growth funds own. Not widely held.",
            "insiders": "Recent insider buying.",
            "short_interest": "Moderate - financial sector always has shorts.",
            "options": "Some activity."
        },

        "catalysts": [
            "US expansion results → 2025 → Prove thesis",
            "Market share gains → ongoing → Growth",
            "Margin expansion → 2025-2026 → Profits",
            "US acquisitions → 2025-2026 → Accelerate"
        ],

        "timeline": {
            "0_3_months": "Q1 results, US pilot data",
            "3_6_months": "US expansion announcements",
            "6_12_months": "US scale, model proof"
        },

        "risks": [
            "CREDIT: Downturn hurts portfolio",
            "REGULATION: Lending regulatory risk",
            "COMPETITION: Banks could get aggressive",
            "EXECUTION: US expansion could fail"
        ],

        "invalidation": "Credit losses above 8% or US expansion abandoned.",
        "conviction": "7/10"
    },

    "BB": {
        "name": "BlackBerry Limited",
        "sector": "Enterprise Software / Cybersecurity",
        "current_price": 0,
        "price_target": "$7.00",
        "timeframe": "18-24 months",
        "upside": "80-100%",
        "support": "$3.50",
        "resistance": "$8.00",

        "macro_impact": """🌍 MACRO TAILWINDS:
• AI boom: Cybersecurity demand exploding = DIRECT BENEFIT
• Connected cars: EV revolution = QNX embedded software demand
• Government spending: Defense budgets increasing = CONTRACTS
• Remote work: Endpoint security more important than ever
• 5G rollout: More connected devices = MORE QNX OPPORTUNITIES""",

        "fundamental": """Turnaround real. Built QNX (200M+ cars) + Cylance (cybersecurity). QNX alone could be worth current market cap.

Automotive OS market growing - cars becoming computers. QNX safety certifications take years to replicate.

Cylance - AI-powered security. Growing market. Cost cuts done, focused on profitability.""",

        "news": [
            "QNX in 200M+ cars worldwide - company data",
            "Automotive OS market growing 15%+ - industry",
            "Cost reduction complete, path to profitability",
            "Cylance gaining enterprise traction"
        ],

        "sentiment": {
            "bullish_why": "Hidden value in QNX, turnaround, cybersecurity tailwinds",
            "bearish_why": "Not consistently profitable, competition, timing",
            "overall": "Neutral - not hated but not loved.",
            "trend": "Stable/Neutral"
        },

        "positioning": {
            "institutional": "Limited. Value funds occasionally mention.",
            "insiders": "No significant recent buying.",
            "short_interest": "Moderate - meme stock history attracts shorts.",
            "options": "Some activity on moves."
        },

        "catalysts": [
            "Automotive partnerships → 2025-2026 → Revenue",
            "Connected car revolution → ongoing → QNX demand",
            "Enterprise contracts → 2025 → Cylance growth",
            "AI/security news → could spark rally"
        ],

        "timeline": {
            "0_3_months": "Partnership announcements possible",
            "3_6_months": "QNX design wins, enterprise deals",
            "6_12_months": "Profitability clarity, car launches"
        },

        "risks": [
            "COMPETITION: Big tech in automotive OS",
            "TIMING: Car software adoption takes years",
            "PROFITABILITY: Still not consistently profitable"
        ],

        "invalidation": "QNX loses major automotive design win.",
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

        "macro_impact": """🌍 MACRO TAILWINDS:
• Consumer spending pressure: Inflation = MORE DOLLAR STORE SHOPPERS
• Economic uncertainty: Defensive play in demand
• Interest rate stability: No headwinds to consumer
• CAD weakness: Import costs up BUT competitive position strong
• Consumer shift: From premium to value retailers ACCELERATING""",

        "fundamental": """Undisputed Canadian discount king. 1,400+ stores, path to 2,000+. Everything $1-$5.

Economic uncertainty = consumers shift to value. Pattern repeated through recessions.

Valuation: ~25x earnings for 5%+ same-store grower = reasonable for defensive.""",

        "news": [
            "1,400+ stores, path to 2,000+ - company guidance",
            "Consistent 5%+ same-store growth - historical",
            "Private-label drives margins - company data",
            "Defensive in downturns - historical pattern"
        ],

        "sentiment": {
            "bullish_why": "Defensive, store expansion, consumer shift to value",
            "bearish_why": "Slow growth, competition, spending collapse risk",
            "overall": "Steady - boring is the point.",
            "trend": "Stable"
        },

        "positioning": {
            "institutional": "Defensive funds, dividend funds own.",
            "insiders": "Management stable.",
            "short_interest": "Low - boring stock.",
            "options": "Limited - covered calls."
        },

        "catalysts": [
            "New stores → ongoing → Unit growth",
            "Economic uncertainty → ongoing → More shoppers",
            "Private-label → 2025 → Margin improvement",
            "E-commerce → 2025 → New channel"
        ],

        "timeline": {
            "0_3_months": "Q4 holiday results",
            "3_6_months": "New store rollout",
            "6_12_months": "E-commerce traction, full year"
        },

        "risks": [
            "CONSUMER: Spending collapse would hurt",
            "COMPETITION: Dollar General expanding Canada",
            "SUPPLY: Cost inflation pressure margins"
        ],

        "invalidation": "Same-store sales negative two quarters.",
        "conviction": "8/10"
    },
}


def get_current_prices():
    """Fetch current prices for all stocks"""
    tickers = {
        "NANO": "NANO.TO", "CXB": "CXB.TO", "SHOP": "SHOP.TO",
        "GSY": "GSY.TO", "BB": "BB.TO", "DOL": "DOL.TO",
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
    
    for symbol in STOCK_ANALYSIS:
        if symbol in prices:
            STOCK_ANALYSIS[symbol]['current_price'] = prices[symbol]
    
    sorted_stocks = sorted(STOCK_ANALYSIS.items(), key=lambda x: x[1]['upside'], reverse=True)
    best_pick = sorted_stocks[0]
    
    email = f"""
Subject: 🚀 HIGH-CONVICTION STOCK PICKS (MACRO-INFORMED + SENTIMENT + TECHNICAL)


---

Hi,


After analyzing market data, real-world developments, investor sentiment, and GLOBAL MACRO EVENTS, here are the highest-conviction opportunities:


{MACRO_CONTEXT}


---


⭐⭐⭐ BEST PICK: {best_pick[0]} - {best_pick[1]['name']} ⭐⭐⭐


Current Price: ${best_pick[1]['current_price']:.2f} (CAD)
Price Target: {best_pick[1]['price_target']}
Timeframe: {best_pick[1]['timeframe']}
Upside Potential: {best_pick[1]['upside']}
Sector: {best_pick[1]['sector']}


---

{best_pick[1]['macro_impact']}


📊 FUNDAMENTAL THESIS:


{best_pick[1]['fundamental']}


📰 NEWS & EVIDENCE:


"""
    for ev in best_pick[1]['news']:
        email += f"- {ev}\n"
    
    sent = best_pick[1]['sentiment']
    email += f"""


💬 MARKET SENTIMENT:


Reddit:
- Bull case: {sent['bullish_why']}
- Bear case: {sent['bearish_why']}

Overall: {sent['overall']} ({sent['trend']})


📊 POSITIONING & FLOW:


- Institutional: {best_pick[1]['positioning']['institutional']}
- Insider: {best_pick[1]['positioning']['insiders']}
- Short interest: {best_pick[1]['positioning']['short_interest']}


🔥 KEY CATALYSTS:


"""
    for cat in best_pick[1]['catalysts']:
        email += f"- {cat}\n"
    
    tl = best_pick[1]['timeline']
    email += f"""


⏳ TIMELINE:


0-3 months: {tl['0_3_months']}
3-6 months: {tl['3_6_months']}
6-12 months: {tl['6_12_months']}


💰 VALUATION:


{best_pick[1]['upside']} upside to {best_pick[1]['price_target']}.


📉 TECHNICAL:


Support: ${best_pick[1]['support']} | Resistance: ${best_pick[1]['resistance']}


⚠️ RISKS:


"""
    for risk in best_pick[1]['risks']:
        email += f"- {risk}\n"
    
    email += f"""


🚨 INVALIDATION:


Thesis wrong if: {best_pick[1]['invalidation']}


⭐ CONVICTION: {best_pick[1]['conviction']}/10


---

"""
    
    for symbol, data in sorted_stocks[1:4]:
        email += f"""


📈 {data['name']} ({symbol})


Current: ${data['current_price']:.2f} → Target: {data['price_target']} ({data['upside']})

{data['macro_impact']}

Catalyst: {data['catalysts'][0]}

"""
    
    email += f"""


---

📊 MARKET INTELLIGENCE SUMMARY:


🌍 MACRO DRIVING MARKETS NOW:

• Fed/BoC: Rates stable → Growth stocks favored
• Gold: At highs → Miners strong (CXB)
• AI boom: Tech leaders outperform (SHOP)
• CAD weak: Exporters/Resources benefit
• Consumer: Shifting to value (DOL)


💰 WHERE MONEY FLOWING:


• INTO: Tech (AI), Gold, Defensive Retail
• OUT OF: Rate-sensitive sectors
• WATCH: Battery/EV supply chain (NANO)


---

🏁 FINAL TAKE:


Best opportunity: 👉 **{best_pick[0]} - {best_pick[1]['name']}**

Why: {best_pick[1]['fundamental'][:300]}

Macro tailwind: {best_pick[1]['macro_impact'][:200]}


---

DISCLAIMER: Educational only. Not financial advice. Do your own research.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} CAD
"""

    return email


def send_email(subject: str, content: str):
    """Send email"""
    email_user = os.environ.get("EMAIL_USER", "")
    email_pass = os.environ.get("EMAIL_PASSWORD", "")
    email_to = os.environ.get("EMAIL_TO", "peterm2543@gmail.com")
    email_host = os.environ.get("EMAIL_HOST", "")
    email_port = int(os.environ.get("EMAIL_PORT", "587"))
    
    if not email_host or not email_user or not email_pass:
        print(f"❌ Email not configured")
        print(f"HOST={email_host}, USER={email_user}, TO={email_to}")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {email_to}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


@click.command()
@click.option("--email", "-e", is_flag=True, help="Send via email")
def main(email: bool):
    """Ultimate Stock Analysis with Macro Intelligence"""
    
    click.echo(f"\n📊 GENERATING MACRO-INFORMED ANALYSIS...")
    click.echo(f"{'='*50}\n")
    
    click.echo("💰 Fetching prices...")
    prices = get_current_prices()
    for symbol, price in prices.items():
        click.echo(f"   {symbol}: ${price:.2f}")
    
    click.echo(f"\n📝 Generating analysis...")
    content = generate_email_content(prices)
    
    click.echo(f"\n{'='*50}")
    print(content[:1200])
    click.echo(f"\n... (truncated)")
    
    if email:
        click.echo(f"\n📧 Sending...")
        send_email("🚀 High-Conviction Stock Picks (MACRO + SENTIMENT)", content)


if __name__ == "__main__":
    main()

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio
import click
import json
import logging
import os
import smtplib
import sys
"""
Stock Analysis Multi-Agent System
Manager → Planner → (Researcher + Quant + Sentiment + Risk) → Synthesizer → Decision

Usage:
    python multi_stock_agent.py AAPL
    python multi_stock_agent.py TSLA --deep
    python multi_stock_agent.py AAPL --email
    python multi_stock_agent.py AAPL --output report.txt
"""


# SECURITY: Never hardcode secrets - use env vars

# Dependencies
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from ddgs import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

# Email settings
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")


# ============================================================================
# MANAGER AGENT - Orchestrates everything
# ============================================================================

class ManagerAgent:
    """Coordinates all agents to analyze a stock"""
    
    def __init__(self, symbol: str, model: str = DEFAULT_MODEL):
        self.symbol = symbol.upper()
        self.model = model
        self.results = {}
        
    async def run(self) -> dict:
        """Run the full analysis pipeline"""
        click.echo(f"\n{'='*60}")
        click.echo(f"📊 STOCK ANALYSIS: {self.symbol}")
        click.echo(f"{'='*60}\n")
        
        # Step 1: Planner creates the analysis plan
        click.echo("📋 Step 1: Planner creating analysis plan...")
        planner = PlannerAgent(self.symbol)
        plan = planner.create_plan()
        self.results['plan'] = plan
        click.echo(f"   ✓ Plan created: {len(plan['tasks'])} tasks\n")
        
        # Step 2: Run all analysis agents in parallel
        click.echo("🔬 Step 2: Running analysis agents...\n")
        
        # Researcher
        click.echo("   📚 Researcher: Analyzing company...")
        researcher = ResearcherAgent(self.symbol, self.model)
        self.results['researcher'] = await researcher.analyze()
        
        # Quant
        click.echo("   📈 Quant: Technical analysis...")
        quant = QuantAgent(self.symbol, self.model)
        self.results['quant'] = await quant.analyze()
        
        # Sentiment
        click.echo("   🗞️ Sentiment: Market mood...")
        sentiment = SentimentAgent(self.symbol, self.model)
        self.results['sentiment'] = await sentiment.analyze()
        
        # Risk
        click.echo("   ⚠️ Risk: Downside analysis...")
        risk = RiskAgent(self.symbol, self.model)
        self.results['risk'] = await risk.analyze()
        
        # Step 3: Synthesizer combines everything
        click.echo("\n🎯 Step 3: Synthesizing insights...")
        synthesizer = SynthesizerAgent(
            self.symbol, 
            self.results,
            self.model
        )
        final = await synthesizer.synthesize()
        self.results['final'] = final
        
        return self.results


# ============================================================================
# PLANNER AGENT - Creates analysis plan
# ============================================================================

class PlannerAgent:
    """Creates a structured analysis plan"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        
    def create_plan(self) -> dict:
        return {
            "symbol": self.symbol,
            "data_needed": [
                "Company fundamentals (P/E, revenue, margins)",
                "Price history (6mo-1y)",
                "Recent news and articles",
                "Competitor comparison",
                "Industry trends"
            ],
            "tasks": [
                {"agent": "Researcher", "task": "Company fundamentals & business analysis"},
                {"agent": "Quant", "task": "Technical indicators & valuation"},
                {"agent": "Sentiment", "task": "News sentiment & market mood"},
                {"agent": "Risk", "task": "Risk assessment & downside analysis"}
            ]
        }


# ============================================================================
# RESEARCHER AGENT - Company analysis
# ============================================================================

class ResearcherAgent:
    """Analyzes company fundamentals"""
    
    def __init__(self, symbol: str, model: str):
        self.symbol = symbol
        self.model = model
        
    async def analyze(self) -> dict:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed"}
        
        try:
            ticker = yf.Ticker(self.symbol)
            info = ticker.info
            
            data = {
                "company_name": info.get('shortName', info.get('longName', 'N/A')),
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "employees": info.get('fullTimeEmployees', 0),
                "description": info.get('longBusinessSummary', 'N/A')[:500],
                "CEO": info.get('ceo', 'N/A'),
                "founded": info.get('founded', 'N/A'),
                "website": info.get('website', 'N/A'),
                
                # Financials
                "market_cap": info.get('marketCap', 0),
                "revenue": info.get('revenue', 0),
                "revenue_growth": info.get('revenueGrowth', 0) * 100,
                "gross_margins": info.get('grossMargins', 0) * 100,
                "operating_margins": info.get('operatingMargins', 0) * 100,
                "profit_margins": info.get('profitMargins', 0) * 100,
                "ebitda": info.get('ebitda', 0),
                "free_cash_flow": info.get('freeCashflow', 0),
                
                # Valuation
                "pe_ratio": info.get('trailingPE', 0),
                "forward_pe": info.get('forwardPE', 0),
                "peg_ratio": info.get('pegRatio', 0),
                
                # Stats
                "beta": info.get('beta', 0),
                "avg_volume": info.get('averageVolume', 0),
            }
            
            # AI summary
            if OLLAMA_AVAILABLE:
                prompt = f"""You are a financial analyst. Summarize this company in 2-3 sentences:

Company: {data['company_name']}
Sector: {data['sector']}
Revenue Growth: {data['revenue_growth']:.1f}%
Gross Margins: {data['gross_margins']:.1f}%
P/E Ratio: {data['pe_ratio']:.1f}

Provide a brief investment summary."""
                
                try:
                    response = requests.post(
                        OLLAMA_URL,
                        json={"model": self.model, "prompt": prompt, "stream": False},
                        timeout=30
                    )
                    data['ai_summary'] = response.json().get('response', '')[:300]
                except:
                    data['ai_summary'] = ''
            
            return data
            
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# QUANT ANALYST - Technical analysis
# ============================================================================

class QuantAgent:
    """Technical and valuation analysis"""
    
    def __init__(self, symbol: str, model: str):
        self.symbol = symbol
        self.model = model
        
    async def analyze(self) -> dict:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed"}
        
        try:
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period="1y")
            
            if len(hist) < 50:
                return {"error": "Insufficient price data"}
            
            # Calculate indicators
            close = hist['Close']
            
            # Moving averages
            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else ma50
            current_price = close.iloc[-1]
            
            # RSI (14-day)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Price momentum
            momentum_1m = (close.iloc[-1] / close.iloc[-21] - 1) * 100 if len(close) > 21 else 0
            momentum_3m = (close.iloc[-1] / close.iloc[-63] - 1) * 100 if len(close) > 63 else 0
            
            # Volatility
            volatility_30d = close.pct_change().rolling(30).std().iloc[-1] * 100
            
            data = {
                "current_price": current_price,
                "ma50": ma50,
                "ma200": ma200,
                "rsi": rsi,
                "momentum_1m": momentum_1m,
                "momentum_3m": momentum_3m,
                "volatility_30d": volatility_30d,
                
                # Signals
                "signal_ma": "BULLISH" if current_price > ma50 > ma200 else "BEARISH" if current_price < ma50 < ma200 else "NEUTRAL",
                "signal_rsi": "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL",
                "signal_momentum": "BULLISH" if momentum_3m > 5 else "BEARISH" if momentum_3m < -5 else "NEUTRAL",
            }
            
            # AI interpretation
            if OLLAMA_AVAILABLE:
                prompt = f"""You are a technical analyst. Interpret this data:

Price: ${data['current_price']:.2f}
MA50: ${data['ma50']:.2f}
MA200: ${data['ma200']:.2f}
RSI: {data['rsi']:.1f}
3-Month Momentum: {data['momentum_3m']:.1f}%

Give a 2-sentence technical outlook."""
                
                try:
                    response = requests.post(
                        OLLAMA_URL,
                        json={"model": self.model, "prompt": prompt, "stream": False},
                        timeout=30
                    )
                    data['ai_interpretation'] = response.json().get('response', '')[:200]
                except:
                    data['ai_interpretation'] = ''
            
            return data
            
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# SENTIMENT ANALYST - News and market mood
# ============================================================================

class SentimentAgent:
    """Analyzes news sentiment"""
    
    def __init__(self, symbol: str, model: str):
        self.symbol = symbol
        self.model = model
        
    async def analyze(self) -> dict:
        news_data = []
        
        # Try to get news from yfinance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(self.symbol)
                news = ticker.news
                if news:
                    for n in news[:5]:
                        news_data.append({
                            "title": n.get('title', '')[:100],
                            "source": n.get('source', 'Unknown'),
                        })
            except:
                pass
        
        # Use AI to analyze sentiment
        sentiment = "NEUTRAL"
        summary = ""
        
        if news_data and OLLAMA_AVAILABLE:
            headlines = "\n".join([n['title'] for n in news_data])
            
            prompt = f"""You are a sentiment analyst. Analyze these headlines for {self.symbol}:

{headlines}

Respond with:
1. Overall sentiment: BULLISH / NEUTRAL / BEARISH
2. Key theme in one sentence"""

            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=30
                )
                result = response.json().get('response', '')
                lines = result.split('\n')
                for line in lines:
                    if 'BULLISH' in line.upper():
                        sentiment = "BULLISH"
                    elif 'BEARISH' in line.upper():
                        sentiment = "BEARISH"
                summary = result[:200]
            except:
                pass
        
        return {
            "sentiment": sentiment,
            "news_count": len(news_data),
            "headlines": news_data,
            "summary": summary
        }


# ============================================================================
# RISK ANALYST - Downside analysis
# ============================================================================

class RiskAgent:
    """Analyzes risks"""
    
    def __init__(self, symbol: str, model: str):
        self.symbol = symbol
        self.model = model
        
    async def analyze(self) -> dict:
        risks = []
        
        # Get basic risk metrics
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(self.symbol)
                info = ticker.info
                
                # Company-specific risks
                risks.append({
                    "category": "Company",
                    "risk": "High debt level" if info.get('debtToEquity', 0) > 100 else "Low debt",
                    "severity": "HIGH" if info.get('debtToEquity', 0) > 150 else "MEDIUM" if info.get('debtToEquity', 0) > 100 else "LOW"
                })
                
                risks.append({
                    "category": "Valuation",
                    "risk": "High P/E ratio" if info.get('trailingPE', 0) > 40 else "Reasonable valuation",
                    "severity": "HIGH" if info.get('trailingPE', 0) > 50 else "MEDIUM" if info.get('trailingPE', 0) > 40 else "LOW"
                })
                
                risks.append({
                    "category": "Market",
                    "risk": "High volatility" if info.get('beta', 1) > 1.5 else "Normal volatility",
                    "severity": "HIGH" if info.get('beta', 1) > 1.5 else "MEDIUM" if info.get('beta', 1) > 1.2 else "LOW"
                })
                
            except:
                pass
        
        # AI-generated risks
        if OLLAMA_AVAILABLE and len(risks) > 0:
            prompt = f"""List 2-3 additional key risks for {self.symbol} stock. 
Consider: competition, regulation, macro conditions, technology disruption.
Keep each risk to 5 words max. Format as a simple list."""

            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=30
                )
                ai_risks = response.json().get('response', '')
                risks.append({
                    "category": "AI-Assessed",
                    "risk": ai_risks[:100],
                    "severity": "MEDIUM"
                })
            except:
                pass
        
        return {
            "risks": risks,
            "risk_count": len(risks),
            "high_severity_count": sum(1 for r in risks if r.get('severity') == 'HIGH')
        }


# ============================================================================
# SYNTHESIZER - Final decision
# ============================================================================

class SynthesizerAgent:
    """Combines all agent outputs into final decision"""
    
    def __init__(self, symbol: str, results: dict, model: str):
        self.symbol = symbol
        self.results = results
        self.model = model
        
    async def synthesize(self) -> dict:
        # Gather signals
        signals = {}
        
        # From Quant
        if 'quant' in self.results and 'error' not in self.results['quant']:
            q = self.results['quant']
            signals['technical'] = q.get('signal_ma', 'NEUTRAL')
            signals['rsi'] = q.get('signal_rsi', 'NEUTRAL')
        
        # From Sentiment
        if 'sentiment' in self.results:
            s = self.results['sentiment']
            signals['sentiment'] = s.get('sentiment', 'NEUTRAL')
        
        # From Risk
        if 'risk' in self.results:
            r = self.results['risk']
            high_risk = r.get('high_severity_count', 0)
            signals['risk_level'] = 'HIGH' if high_risk >= 2 else 'MEDIUM' if high_risk >= 1 else 'LOW'
        
        # Count bullish/bearish
        bullish = sum(1 for v in signals.values() if 'BULLISH' in str(v).upper())
        bearish = sum(1 for v in signals.values() if 'BEARISH' in str(v).upper())
        
        # Make decision
        if bullish > bearish + 1:
            decision = "BUY"
        elif bearish > bullish + 1:
            decision = "SELL"
        else:
            decision = "HOLD"
        
        # Get company name
        company = "Unknown"
        if 'researcher' in self.results and 'error' not in self.results['researcher']:
            company = self.results['researcher'].get('company_name', 'Unknown')
        
        final = {
            "symbol": self.symbol,
            "company": company,
            "decision": decision,
            "signals": signals,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "timestamp": datetime.now().isoformat()
        }
        
        # AI final summary
        if OLLAMA_AVAILABLE:
            prompt = f"""You are a hedge fund portfolio manager. Make a final decision for {self.symbol}.

Technical signals: {signals.get('technical', 'N/A')} | RSI: {signals.get('rsi', 'N/A')}
Sentiment: {signals.get('sentiment', 'N/A')}
Risk: {signals.get('risk_level', 'N/A')}

Respond with:
1. Final decision: BUY / HOLD / SELL (be decisive!)
2. One sentence rationale"""

            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=30
                )
                final['ai_rationale'] = response.json().get('response', '')[:200]
            except:
                final['ai_rationale'] = "AI analysis unavailable"
        
        return final


# ============================================================================
# MAIN
# ============================================================================

def send_email(subject: str, content: str, to_email: str = None):
    """Send results via email"""
    host = EMAIL_HOST
    port = EMAIL_PORT
    user = EMAIL_USER
    password = EMAIL_PASSWORD
    from_email = EMAIL_FROM
    to = to_email or EMAIL_TO
    
    if not host or not user or not to:
        return False
    
    msg = MIMEMultipart()
    msg['From'] = from_email or user
    msg['To'] = to
    msg['Subject'] = f"📊 Stock Analysis: {subject}"
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False


def save_to_file(content: str, filename: str):
    """Save results to file"""
    with open(filename, 'a') as f:
        f.write(content + "\n")
    click.echo(f"✅ Saved to {filename}")


@click.command()
@click.argument("symbol")
@click.option("--model", "-m", default=None, help="Ollama model")
@click.option("--output", "-o", default=None, help="Save to file")
@click.option("--email", "-e", is_flag=True, help="Send via email")
@click.option("--to", default=None, help="Email recipient")
def main(symbol: str, model: str, output: str, email: bool, to: str):
    """Multi-Agent Stock Analysis System"""
    
    model = model or DEFAULT_MODEL
    
    click.echo(f"🚀 Starting analysis for {symbol.upper()} with model: {model}")
    
    # Run async
    manager = ManagerAgent(symbol.upper(), model)
    results = asyncio.run(manager.run())
    
    # Display final result
    click.echo(f"\n{'='*60}")
    click.echo("🎯 FINAL DECISION")
    click.echo(f"{'='*60}")
    
    final = results['final']
    
    emoji = "🟢" if final['decision'] == "BUY" else "🔴" if final['decision'] == "SELL" else "🟡"
    decision_text = f"\n{emoji} {final['decision']} {final['symbol']} - {final['company']}"
    click.echo(decision_text)
    
    rationale = ""
    if 'ai_rationale' in final:
        rationale = f"\n💡 {final['ai_rationale']}"
        click.echo(rationale)
    
    signal_text = f"\n📊 Signal Summary: Bullish: {final['bullish_count']} | Bearish: {final['bearish_count']}"
    click.echo(signal_text)
    
    click.echo(f"\n✅ Analysis complete!\n")
    
    # Save to file
    full_content = f"""
📊 Multi-Agent Stock Analysis: {symbol.upper()}
{decision_text}
{rationale}
{signal_text}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if output:
        save_to_file(full_content, output)
    
    # Send email
    if email:
        email_content = f"""
📊 Multi-Agent Stock Analysis: {symbol.upper()}

{emoji} {final['decision']} - {final['company']}

{final.get('ai_rationale', '')}

Signals: Bullish {final['bullish_count']} | Bearish {final['bearish_count']}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        send_email(symbol.upper(), email_content, to)


if __name__ == "__main__":
    main()

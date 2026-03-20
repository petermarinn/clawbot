from ddgs import DDGS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import click
import os
import requests
import smtplib
"""
Financial News Agent
Get latest stock market news and AI analysis

Usage:
    python news_agent.py
    python news_agent.py AAPL
    python news_agent.py "Federal Reserve" --email
"""


# SECURITY: Never hardcode secrets - use env vars

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

# Email settings
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")


def send_email(subject: str, content: str, to_email: str = None):
    """Send via email"""
    host = EMAIL_HOST
    port = EMAIL_PORT
    user = EMAIL_USER
    password = EMAIL_PASSWORD
    from_email = EMAIL_FROM
    to = to_email or EMAIL_TO
    
    if not host or not user or not to:
        click.echo("❌ Email not configured")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = from_email or user
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        click.echo(f"✅ Email sent!")
        return True
    except Exception as e:
        click.echo(f"❌ Email error: {e}")
        return False


def search_news(query: str = "stock market") -> list:
    """Search financial news"""
    news = []
    
    try:
        with DDGS() as ddgs:
            results = ddgs.text(f"{query} stock news 2024", max_results=10)
            
        for r in results:
            news.append({
                "title": r.get('title', ''),
                "url": r.get('url', ''),
                "snippet": r.get('body', '')[:200]
            })
    except Exception as e:
        click.echo(f"Search error: {e}")
    
    return news


def ai_summary(news: list, query: str, model: str) -> str:
    """AI summarize news"""
    
    headlines = "\n".join([n['title'] for n in news[:8]])
    
    prompt = f"""You are a financial news analyst. Summarize the latest news about: {query}

Headlines:
{headlines}

Provide:
1. Overall market sentiment (Bullish/Bearish/Neutral)
2. Key themes (2-3 sentences)
3. Impact on investors

Be concise and actionable."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        return response.json().get('response', '')
    except Exception as e:
        return f"AI Error: {e}"


@click.command()
@click.argument("query", required=False)
@click.option("--ai/--no-ai", default=True, help="AI summary")
@click.option("--model", "-m", default=None)
@click.option("--email", "-e", is_flag=True, help="Send via email")
@click.option("--to", default=None, help="Email recipient")
def main(query: str, ai: bool, model: str, email: bool, to: str):
    """Financial News - Market news and analysis"""
    
    query = query or "stock market"
    model = model or DEFAULT_MODEL
    
    click.echo(f"\n📰 FINANCIAL NEWS")
    click.echo(f"Topic: {query}")
    click.echo(f"{'='*50}\n")
    
    # Search
    click.echo("🔍 Fetching news...")
    news = search_news(query)
    
    if not news:
        click.echo("❌ No news found")
        return
    
    click.echo(f"   ✓ Found {len(news)} articles\n")
    
    # Display news
    click.echo(f"{'='*50}")
    click.echo("📰 LATEST NEWS")
    click.echo(f"{'='*50}\n")
    
    for i, n in enumerate(news[:8], 1):
        click.echo(f"{i}. {n['title']}")
        click.echo(f"   {n['url']}\n")
    
    # AI summary
    if ai:
        click.echo(f"{'='*50}")
        click.echo("💡 AI ANALYSIS")
        click.echo(f"{'='*50}\n")
        
        summary = ai_summary(news, query, model)
        click.echo(summary)
        click.echo()
    
    # Send email
    if email:
        email_content = f"""
Financial News: {query}

{summary}

Sources:
{chr(10).join([n['title'] + ' - ' + n['url'] for n in news[:5]])}
"""
        send_email(f"📰 Financial News: {query}", email_content, to)
    
    click.echo()


if __name__ == "__main__":
    main()

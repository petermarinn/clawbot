"""
Price Alert Agent
Set price alerts for stocks

Usage:
    python alert_agent.py add AAPL 180
    python alert_agent.py add TSLA 150 above
    python alert_agent.py list
    python alert_agent.py check
    python alert_agent.py check --email
"""

import click
import json
import os
import time
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

ALERT_FILE = "alerts.json"

# Email settings
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "peterm2543@gmail.com")


def load_alerts():
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE) as f:
            return json.load(f)
    return []


def save_alerts(alerts):
    with open(ALERT_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)


def send_email(subject: str, content: str, to_email: str = None):
    """Send alert via email"""
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
    msg['Subject'] = subject
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


def check_alerts(email: bool = False, to_email: str = None):
    """Check all alerts and return triggered ones"""
    alerts = load_alerts()
    triggered = []
    message = "PRICE ALERT TRIGGERED\n\n"
    
    for alert in alerts:
        symbol = alert['symbol']
        target = alert['target_price']
        direction = alert['direction']
        
        try:
            ticker = yf.Ticker(symbol)
            current = ticker.info.get('currentPrice', 0)
            
            if direction == 'above' and current >= target:
                triggered.append({
                    **alert,
                    'current_price': current,
                    'triggered_at': datetime.now().isoformat()
                })
                message += f"ALERT: {symbol} hit ${current:.2f} (above ${target})\n"
            elif direction == 'below' and current <= target:
                triggered.append({
                    **alert,
                    'current_price': current,
                    'triggered_at': datetime.now().isoformat()
                })
                message += f"ALERT: {symbol} dropped to ${current:.2f} (below ${target})\n"
        except:
            pass
    
    # Send email if triggered and requested
    if triggered and email:
        send_email("🚨 Stock Price Alert!", message, to_email)
    
    return triggered


@click.group()
def cli():
    """Price Alert - Monitor stock prices"""
    pass


@cli.command()
@click.argument("symbol")
@click.argument("price", type=float)
@click.option("--direction", "-d", default="above", help="above or below")
def add(symbol: str, price: float, direction: str):
    """Add alert: SYMBOL PRICE [above/below]"""
    alerts = load_alerts()
    
    alerts.append({
        "id": len(alerts) + 1,
        "symbol": symbol.upper(),
        "target_price": price,
        "direction": direction,
        "created": datetime.now().isoformat(),
        "triggered": False
    })
    
    save_alerts(alerts)
    click.echo(f"✅ Alert added: {symbol.upper()} {direction} ${price}")


@cli.command()
def list():
    """List all alerts"""
    alerts = load_alerts()
    
    if not alerts:
        click.echo("🔔 No alerts set!")
        click.echo("   python alert_agent.py add AAPL 180")
        return
    
    click.echo(f"\n🔔 PRICE ALERTS ({len(alerts)})")
    click.echo("="*50)
    
    for a in alerts:
        emoji = "⬆️" if a['direction'] == 'above' else "⬇️"
        status = "✅ TRIGGERED" if a.get('triggered') else "⏳ Active"
        click.echo(f"{a['id']}. {a['symbol']} {emoji} ${a['target_price']} - {status}")
    
    click.echo()


@cli.command()
@click.option("--email", "-e", is_flag=True, help="Send email if triggered")
@click.option("--to", default=None, help="Email recipient")
def check(email: bool, to: str):
    """Check alerts"""
    alerts = load_alerts()
    
    if not alerts:
        click.echo("🔔 No alerts to check")
        return
    
    click.echo("🔍 Checking alerts...\n")
    
    triggered = check_alerts(email, to)
    
    if triggered:
        click.echo("🚨 TRIGGERED ALERTS:")
        for t in triggered:
            click.echo(f"   ⚠️ {t['symbol']} is ${t['current_price']:.2f} (target: ${t['target_price']})")
        
        # Mark as triggered
        for t in triggered:
            for a in alerts:
                if a['id'] == t['id']:
                    a['triggered'] = True
        save_alerts(alerts)
    else:
        click.echo("✅ No alerts triggered yet")
    
    # Show current prices
    click.echo("\n📊 Current Prices:")
    for a in alerts:
        try:
            ticker = yf.Ticker(a['symbol'])
            price = ticker.info.get('currentPrice', 0)
            emoji = "⬆️" if a['direction'] == 'above' else "⬇️"
            click.echo(f"   {a['symbol']}: ${price:.2f} (alert: {emoji} ${a['target_price']})")
        except:
            pass
    
    click.echo()


@cli.command()
@click.argument("alert_id", type=int)
def delete(alert_id: int):
    """Delete alert"""
    alerts = load_alerts()
    alerts = [a for a in alerts if a['id'] != alert_id]
    save_alerts(alerts)
    click.echo(f"✅ Alert {alert_id} deleted")


@cli.command()
def clear():
    """Clear all alerts"""
    save_alerts([])
    click.echo("✅ All alerts cleared")


if __name__ == "__main__":
    cli()

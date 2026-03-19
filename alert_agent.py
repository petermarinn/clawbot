"""
Price Alert Agent
Set price alerts for stocks

Usage:
    python alert_agent.py add AAPL 180
    python alert_agent.py add TSLA 150 above
    python alert_agent.py list
    python alert_agent.py check
    python alert_agent.py check --discord
"""

import click
import json
import os
import time
import yfinance as yf
import requests
from datetime import datetime

ALERT_FILE = "alerts.json"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")


def load_alerts():
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE) as f:
            return json.load(f)
    return []


def save_alerts(alerts):
    with open(ALERT_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)


def send_discord(message: str, webhook_url: str = None):
    """Send alert to Discord"""
    url = webhook_url or DISCORD_WEBHOOK
    if not url:
        return False
    
    data = {"content": message}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 204
    except:
        return False


def check_alerts(discord: bool = False, webhook: str = None):
    """Check all alerts and return triggered ones"""
    alerts = load_alerts()
    triggered = []
    message = "🚨 **PRICE ALERT TRIGGERED**\n\n"
    
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
                message += f"⚠️ **{symbol}** hit ${current:.2f} (above ${target})\n"
            elif direction == 'below' and current <= target:
                triggered.append({
                    **alert,
                    'current_price': current,
                    'triggered_at': datetime.now().isoformat()
                })
                message += f"⚠️ **{symbol}** dropped to ${current:.2f} (below ${target})\n"
        except:
            pass
    
    # Send Discord if triggered and requested
    if triggered and discord:
        send_discord(message, webhook)
    
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
@click.option("--discord", "-d", is_flag=True, help="Send to Discord if triggered")
@click.option("--webhook", "-w", default=None, help="Discord webhook URL")
def check(discord: bool, webhook: str):
    """Check alerts"""
    alerts = load_alerts()
    
    if not alerts:
        click.echo("🔔 No alerts to check")
        return
    
    click.echo("🔍 Checking alerts...\n")
    
    triggered = check_alerts(discord, webhook)
    
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

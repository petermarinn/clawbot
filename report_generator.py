#!/usr/bin/env python3
"""
Report Generator - Professional Investment Reports
Generates HTML email reports with stock picks, price targets, and source citations
"""
import os
from datetime import datetime

# Import data intelligence
try:
    from data_intelligence import DataIntelligence
except ImportError:
    DataIntelligence = None


class ReportGenerator:
    def __init__(self):
        self.intelligence = DataIntelligence() if DataIntelligence else None
        self.report_config = {
            "title": "Clawbot Stock Intelligence Report",
            "logo": "🤖",
            "disclaimer": "This report is for informational purposes only and does not constitute financial advice.",
        }
    
    def generate_header(self) -> str:
        """Generate report header"""
        return f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px; border-radius: 10px 10px 0 0;">
            <h1 style="color: #00d4ff; margin: 0; font-size: 28px;">
                {self.report_config['logo']} {self.report_config['title']}
            </h1>
            <p style="color: #8b949e; margin: 10px 0 0 0;">
                Generated: {datetime.now().strftime('%B %d, %Y at %H:%M EST')}
            </p>
        </div>
        """
    
    def generate_top_picks_section(self, picks: List[Dict]) -> str:
        """Generate top picks section"""
        if not picks:
            return "<p>No picks available at this time.</p>"
        
        html = '<div style="padding: 20px;">'
        html += '<h2 style="color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px;">🎯 Top Picks</h2>'
        
        for i, pick in enumerate(picks[:3], 1):
            symbol = pick.get("symbol", "?")
            rec = pick.get("recommendation", "HOLD")
            conf = pick.get("confidence", "NEUTRAL")
            score = pick.get("alignment_score", 0)
            
            # Color based on recommendation
            if rec == "BUY":
                color = "#3fb950"
                emoji = "🟢"
            elif rec == "SELL":
                color = "#f85149"
                emoji = "🔴"
            else:
                color = "#d29922"
                emoji = "🟡"
            
            # Get market data for this stock
            market = pick.get("market", {})
            price = market.get("price", 0)
            target = market.get("target", 0)
            change = market.get("change_pct", 0)
            
            upside = ((target - price) / price * 100) if price and target else 0
            
            html += f'''
            <div style="background: #21262d; border-radius: 8px; padding: 20px; margin: 15px 0; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 24px; font-weight: bold; color: #c9d1d9;">{i}. {symbol}</span>
                        <span style="color: {color}; font-size: 18px; margin-left: 10px;">{emoji} {rec}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #8b949e; font-size: 12px;">Confidence</div>
                        <div style="color: {color}; font-weight: bold;">{conf}</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 15px; color: #8b949e;">
                    <div>
                        <div style="font-size: 12px;">Current Price</div>
                        <div style="color: #c9d1d9; font-size: 18px;">${price:.2f}</div>
                    </div>
                    <div>
                        <div style="font-size: 12px;">Target Price</div>
                        <div style="color: #c9d1d9; font-size: 18px;">${target:.2f}</div>
                    </div>
                    <div>
                        <div style="font-size: 12px;">Today's Change</div>
                        <div style="color: {'#3fb950' if change > 0 else '#f85149'}; font-size: 18px;">{change:+.2f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 12px;">Upside</div>
                        <div style="color: #3fb950; font-size: 18px;">{upside:+.1f}%</div>
                    </div>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #30363d;">
                    <div style="color: #8b949e; font-size: 12px;">Alignment Score</div>
                    <div style="background: #30363d; border-radius: 10px; height: 20px; width: 100%; margin-top: 5px;">
                        <div style="background: {color}; border-radius: 10px; height: 100%; width: {score*100:.0f}%;"></div>
                    </div>
                </div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def generate_stocks_section(self) -> str:
        """Generate all stocks section"""
        if not self.intelligence:
            return "<p>Data intelligence not available.</p>"
        
        html = '<div style="padding: 20px; background: #0d1117;">'
        html += '<h2 style="color: #58a6ff; border-bottom: 2px solid #58a6ff; padding-bottom: 10px;">📈 All Tracked Stocks</h2>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #21262d;"><th style="padding: 12px; text-align: left; color: #8b949e;">Symbol</th><th style="padding: 12px; text-align: right; color: #8b949e;">Price</th><th style="padding: 12px; text-align: right; color: #8b949e;">Change</th><th style="padding: 12px; text-align: right; color: #8b949e;">Target</th><th style="padding: 12px; text-align: right; color: #8b949e;">Rating</th></tr>'
        
        stocks = ["NANO", "WPM", "SHOP", "BB", "GSY", "DOL"]
        
        for symbol in stocks:
            if self.intelligence:
                market = self.intelligence.fetch_market_data(symbol)
                if "error" not in market:
                    price = market.get("price", 0)
                    change = market.get("change_pct", 0)
                    target = market.get("target_mean_price", 0)
                    rating = market.get("recommendation", "N/A")
                    
                    change_color = "#3fb950" if change > 0 else "#f85149"
                    
                    html += f'''<tr style="border-bottom: 1px solid #30363d;">
                        <td style="padding: 12px; color: #c9d1d9; font-weight: bold;">{symbol}</td>
                        <td style="padding: 12px; text-align: right; color: #c9d1d9;">${price:.2f}</td>
                        <td style="padding: 12px; text-align: right; color: {change_color};">{change:+.2f}%</td>
                        <td style="padding: 12px; text-align: right; color: #c9d1d9;">${target:.2f}</td>
                        <td style="padding: 12px; text-align: right; color: #58a6ff;">{rating}</td>
                    </tr>'''
        
        html += '</table></div>'
        return html
    
    def generate_footer(self) -> str:
        """Generate report footer"""
        return f'''
        <div style="padding: 20px; background: #161b22; border-radius: 0 0 10px 10px; text-align: center;">
            <p style="color: #8b949e; font-size: 12px; margin: 0;">
                {self.report_config['disclaimer']}
            </p>
            <p style="color: #484f58; font-size: 11px; margin: 10px 0 0 0;">
                🤖 Clawbot Stock Intelligence • Auto-generated by AI Agents
            </p>
        </div>
        '''
    
    def generate_html_report(self) -> str:
        """Generate complete HTML report"""
        picks = []
        if self.intelligence:
            picks = self.intelligence.get_top_picks()
        
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report_config['title']}</title>
</head>
<body style="margin: 0; padding: 0; background: #0d1117; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;">
    <div style="max-width: 800px; margin: 0 auto; background: #0d1117;">
        {self.generate_header()}
        {self.generate_top_picks_section(picks)}
        {self.generate_stocks_section()}
        {self.generate_footer()}
    </div>
</body>
</html>
        '''
        
        return html
    
    def generate_text_report(self) -> str:
        """Generate plain text report"""
        if not self.intelligence:
            return "Data intelligence not available."
        
        lines = []
        lines.append("=" * 60)
        lines.append("🤖 CLAWBOT STOCK INTELLIGENCE REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M EST')}")
        lines.append("")
        
        # Top picks
        picks = self.intelligence.get_top_picks()
        
        if picks:
            lines.append("🎯 TOP PICKS:")
            lines.append("-" * 40)
            
            for pick in picks[:3]:
                symbol = pick.get("symbol")
                rec = pick.get("recommendation")
                conf = pick.get("confidence")
                market = pick.get("market", {})
                price = market.get("price", 0)
                target = market.get("target", 0)
                
                upside = ((target - price) / price * 100) if price and target else 0
                
                lines.append(f"  {symbol}: {rec} (Confidence: {conf})")
                lines.append(f"    Price: ${price:.2f} → Target: ${target:.2f} ({upside:+.1f}% upside)")
            
            lines.append("")
        
        # All stocks
        lines.append("📈 ALL TRACKED STOCKS:")
        lines.append("-" * 40)
        
        stocks = ["NANO", "WPM", "SHOP", "BB", "GSY", "DOL"]
        
        for symbol in stocks:
            market = self.intelligence.fetch_market_data(symbol)
            if "error" not in market:
                price = market.get("price", 0)
                change = market.get("change_pct", 0)
                target = market.get("target_mean_price", 0)
                rating = market.get("recommendation", "N/A")
                
                lines.append(f"  {symbol}: ${price:.2f} ({change:+.2f}%) Target: ${target:.2f} [{rating}]")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("Disclaimer: This report is for informational purposes only.")
        
        return "\n".join(lines)
    
    def save_report(self, filename: str = None):
        """Save report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/report_{timestamp}.html"
        
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)
        
        html = self.generate_html_report()
        
        with open(filename, 'w') as f:
            f.write(html)
        
        print(f"✅ Report saved to: {filename}")
        return filename
    
    def send_email(self, recipients: List[str], subject: str = None):
        """Send report via email (requires SMTP configuration)"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get SMTP config from environment
        smtp_host = os.environ.get("SMTP_HOST", "")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")
        
        if not smtp_host or not smtp_user:
            print("⚠️  SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASS environment variables.")
            print("   Saving report to file instead.")
            return self.save_report()
        
        if not subject:
            subject = f"🤖 Clawbot Report - {datetime.now().strftime('%B %d, %Y')}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = ", ".join(recipients)
        
        # Attach both text and HTML versions
        text_part = MIMEText(self.generate_text_report(), 'plain')
        html_part = MIMEText(self.generate_html_report(), 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send
        try:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipients, msg.as_string())
            server.quit()
            
            print(f"✅ Report sent to: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Report Generator")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--text", action="store_true", help="Generate text report")
    parser.add_argument("--save", type=str, help="Save to file")
    parser.add_argument("--send", action="store_true", help="Send via email")
    parser.add_argument("--to", type=str, help="Email recipients (comma-separated)")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
    if args.html:
        print(generator.generate_html_report())
    elif args.text:
        print(generator.generate_text_report())
    elif args.save:
        generator.save_report(args.save)
    elif args.send:
        if not args.to:
            print("❌ Please specify --to email address")
            return
        recipients = [r.strip() for r in args.to.split(",")]
        generator.send_email(recipients)
    else:
        # Default: save and show
        generator.save_report()
        print("\n" + generator.generate_text_report())


if __name__ == "__main__":
    main()

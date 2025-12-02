import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
# Debug: print loaded credentials (remove in production)
print(f"DEBUG: sender_email={os.getenv('SENDER_EMAIL')}, recipient_email={os.getenv('RECIPIENT_EMAIL')}")

class EmailNotifier:
    def __init__(self):
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.recipient_email = os.getenv("RECIPIENT_EMAIL", "dealsbydelulu@gmail.com")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    async def send_alert(self, recommendations):
        """Send email alert for Buy/Strong Buy and Sell/Strong Sell recommendations"""
        if not self.sender_email or not self.sender_password:
            print("Email credentials not configured. Skipping email notification.")
            return

        # Filter for Buy signals (confidence >= 65) and Sell signals (confidence <= 45)
        buy_signals = [r for r in recommendations if r["recommendation"] in ["Buy", "Strong Buy"]]
        sell_signals = [r for r in recommendations if r["recommendation"] in ["Sell", "Strong Sell"]]

        if not buy_signals and not sell_signals:
            return  # Nothing to notify

        # Create email
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🚀 Stock Advisor Alert: {len(buy_signals)} Buy Signal{'s' if len(buy_signals) != 1 else ''}"
        message["From"] = self.sender_email
        message["To"] = self.recipient_email

        # HTML body
        html = self._create_html_body(buy_signals, sell_signals)
        part = MIMEText(html, "html")
        message.attach(part)

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.sender_email,
                password=self.sender_password,
            )
            print(f"Email sent to {self.recipient_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def _create_html_body(self, buy_signals, sell_signals):
        """Create HTML email body"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #0f172a; color: #fff; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; }
                h1 { color: #38bdf8; }
                .stock-card { background: #1e293b; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid #22c55e; }
                .sell-card { border-left-color: #ef4444; }
                .ticker { font-size: 20px; font-weight: bold; }
                .price { color: #22c55e; }
                .confidence { color: #38bdf8; font-weight: bold; }
                .reasoning { font-size: 12px; color: #94a3b8; margin-top: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📈 Stock Advisor Alert</h1>
        """

        if buy_signals:
            html += f"<h2>🚀 {len(buy_signals)} Buy Signal{'s' if len(buy_signals) > 1 else ''}</h2>"
            for stock in buy_signals[:5]:  # Limit to top 5
                html += f"""
                <div class="stock-card">
                    <div class="ticker">{stock['ticker']}</div>
                    <div class="price">${stock['price']:.2f} ({stock['change_percent']:+.2f}%)</div>
                    <div class="confidence">Confidence: {stock['confidence_score']:.1f}%</div>
                    <div class="reasoning">
                        {'<br>'.join(stock['reasoning'][:3])}
                    </div>
                </div>
                """

        if sell_signals:
            html += f"<h2>⚠️ {len(sell_signals)} Sell Signal{'s' if len(sell_signals) > 1 else ''}</h2>"
            for stock in sell_signals[:5]:  # Limit to top 5
                html += f"""
                <div class="stock-card sell-card">
                    <div class="ticker">{stock['ticker']}</div>
                    <div class="price">${stock['price']:.2f} ({stock['change_percent']:+.2f}%)</div>
                    <div class="confidence">Confidence: {stock['confidence_score']:.1f}%</div>
                    <div class="reasoning">
                        {'<br>'.join(stock['reasoning'][:3])}
                    </div>
                </div>
                """

        html += """
                <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">
                    This is an automated alert from your Stock Advisor. 
                    Always do your own research before making investment decisions.
                </p>
            </div>
        </body>
        </html>
        """
        return html

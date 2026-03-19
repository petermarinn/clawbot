# Clawbot - Autonomous Stock Intelligence Dashboard

A real-time, self-updating, AI-powered stock platform built with Flask.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Clawbot+Dashboard)

## Features

- 📊 **Real-time Stock Data** - Auto-refreshing every 30 seconds
- 📈 **Interactive Charts** - Multiple timeframes (1D, 1W, 1M, 3M, 1Y)
- 🔔 **Price Alerts** - Set custom alerts for your stocks
- 💡 **Stock Analysis** - Entry zones, stop losses, price targets
- 📰 **Sentiment Tracking** - Reddit, Twitter, Stocktwits
- 🎯 **Top Pick** - Highest conviction stock recommendation

## Current Stocks Tracked

| Symbol | Name | Sector | Target |
|--------|------|--------|--------|
| NANO | Nano One Materials | Battery Technology | $3.65 |
| WPM | Wheaton Precious Metals | Precious Metals Streaming | $95 |
| SHOP | Shopify Inc | E-commerce | $225 |
| BB | BlackBerry Ltd | Enterprise Software | $7.00 |
| GSY | goeasy Ltd | Fintech | $175 |
| DOL | Dollarama Inc | Retail | $175 |

## Quick Start

### Local Development

```bash
# Clone the repo
git clone https://github.com/petermarinn/clawbot.git
cd clawbot

# Install dependencies
pip install -r requirements.txt

# Run the app
python web_app.py

# Open http://localhost:5000
```

### Requirements

- Python 3.8+
- flask
- flask-cors
- yfinance
- requests

## Deployment on Linux Server

### Option 1: Manual Deployment

1. Copy the files to your server:
   ```bash
   rsync -avz --exclude='.git' ./clawbot user@your-server:/opt/clawbot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python web_app.py &
   ```

### Option 2: Automatic Deployment with deploy.sh

The `deploy.sh` script automatically pulls the latest code from GitHub and restarts the application.

1. Copy deploy.sh to your server:
   ```bash
   scp deploy.sh user@your-server:/opt/clawbot/
   ```

2. Run manually:
   ```bash
   bash /opt/clawbot/deploy.sh
   ```

3. Set up a cron job for automatic updates (optional):
   ```bash
   # Edit crontab
   crontab -e
   
   # Add this line to check for updates every hour
   0 * * * * cd /opt/clawbot && git pull origin main && /opt/clawbot/deploy.sh >> /var/log/clawbot_cron.log 2>&1
   ```

### Option 3: Systemd Service

Create a systemd service for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/clawbot.service

# Add:
[Unit]
Description=Clawbot Stock Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/clawbot
ExecStart=/usr/bin/python3 /opt/clawbot/web_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable clawbot
sudo systemctl start clawbot
```

## Usage

- **View Dashboard**: Open `http://your-server:5000`
- **Add Alert**: Select stock, condition (above/below), target price, click +
- **View Chart**: Click any stock card to see detailed charts
- **Change Timeframe**: Use buttons (1D, 1W, 1M, 3M, 1Y)

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/stocks` | Get all stock data |
| `/api/market` | Get market indices |
| `/api/chart/<symbol>` | Get chart data |
| `/api/alerts` | Get/set price alerts |

## License

MIT License

## Author

Peter Marinn

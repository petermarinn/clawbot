#!/bin/bash
# setup-auto-deploy.sh - Run this on your Linux server to enable auto-deployment
# This will set up cron to automatically pull and deploy updates every hour

echo "Setting up auto-deployment for Clawbot..."

# Get the directory where the script is located
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if it's a git repo
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Not a git repository. Cloning from GitHub..."
    cd ~
    git clone https://github.com/petermarinn/clawbot.git
    APP_DIR="$HOME/clawbot"
fi

cd $APP_DIR

# Check if requirements are installed
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt -q
fi

# Create the cron job
echo "Setting up cron job for auto-deployment..."

# Remove existing clawbot cron entries
crontab -l 2>/dev/null | grep -v "clawbot" > /tmp/current_cron

# Add new cron job - runs every hour
echo "0 * * * * cd $APP_DIR && git pull origin main 2>&1 | logger -t clawbot-deploy && pkill -f web_app.py && python3 web_app.py > /dev/null 2>&1 &" >> /tmp/current_cron

# Install new crontab
crontab /tmp/current_cron
rm /tmp/current_cron

echo "✅ Auto-deployment set up!"
echo "   - Will check for updates every hour"
echo "   - Pulls from GitHub and restarts the app automatically"
echo "   - Logs are sent to system logger"

# Show current cron
echo ""
echo "Current cron jobs:"
crontab -l | grep clawbot

echo ""
echo "To test immediately, run:"
echo "   cd $APP_DIR && git pull origin main && python3 web_app.py &"

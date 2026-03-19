#!/bin/bash
# deploy.sh - Pull latest code from GitHub and restart the application
# Run this script on your Linux server to deploy updates

REPO_URL="https://github.com/petermarinn/clawbot.git"
APP_DIR="/opt/clawbot"
SERVICE_NAME="clawbot"

echo "=========================================="
echo "Clawbot Deployment Script"
echo "=========================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt-get update && apt-get install -y git
fi

# Create app directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
    echo "Creating app directory..."
    mkdir -p $APP_DIR
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    
    # Create virtual environment (optional but recommended)
    # python3 -m venv venv
    # source venv/bin/activate
else
    echo "Pulling latest changes..."
    cd $APP_DIR
    git pull origin main
fi

# Check if requirements.txt changed
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
fi

# Restart the service if it exists (systemd)
if command -v systemctl &> /dev/null; then
    echo "Restarting service..."
    systemctl restart $SERVICE_NAME || echo "Service not found, starting manually..."
    
    # If no systemd service, try to start manually
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        pkill -f web_app.py || true
        nohup python3 web_app.py > /var/log/clawbot.log 2>&1 &
        echo "Started web_app.py in background"
    fi
else
    # No systemctl, just restart the app
    echo "Restarting application..."
    pkill -f web_app.py || true
    sleep 2
    nohup python3 web_app.py > /var/log/clawbot.log 2>&1 &
    echo "Started web_app.py in background"
fi

echo "=========================================="
echo "Deployment complete!"
echo "App should be running at: http://localhost:5000"
echo "=========================================="

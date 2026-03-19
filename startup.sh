#!/bin/bash
# startup.sh - Start the Clawbot autonomous system

echo "🚀 Starting Clawbot Autonomous System..."

# Install dependencies if needed
pip3 install flask flask-cors yfinance requests 2>/dev/null

# Kill any existing processes
pkill -f "python3 web_app.py" 2>/dev/null
pkill -f "python3 run_system.py" 2>/dev/null

# Start web server in background
echo "🌐 Starting web server..."
cd ~/clawbot
python3 web_app.py > /tmp/webapp.log 2>&1 &
sleep 2

# Start commander in background
echo "🎖️  Starting Commander..."
python3 run_system.py --continuous --interval 60 > /tmp/commander.log 2>&1 &

sleep 3

echo ""
echo "✅ System started!"
echo ""
echo "Web UI: http://localhost:5000"
echo "API:    http://localhost:5000/api/memory"
echo ""
echo "To stop: pkill -f 'python3'"

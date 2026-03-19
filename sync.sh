#!/bin/bash
# Auto-sync script - pulls latest from GitHub
# Add to crontab: */5 * * * * /home/peterm2543/clawbot/sync.sh >> /home/peterm2543/clawbot/sync.log 2>&1

cd ~/clawbot

# Pull latest from GitHub
git pull origin main

# If there were changes, run the scraper or other tasks
if [ $? -eq 0 ]; then
    echo "$(date): Synced successfully"
else
    echo "$(date): Sync failed"
fi

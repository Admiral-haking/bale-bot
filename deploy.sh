#!/bin/bash
# Deploy Bale Bot - Tab Ahmadi
# usage: ./deploy.sh [polling|webhook]

set -e

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-polling}"
LOG_FILE="$BOT_DIR/logs/deploy.log"

mkdir -p "$BOT_DIR/logs"

log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

log "Starting deployment..."

# Step 1: Pull latest from git
if [ -d "$BOT_DIR/.git" ]; then
    log "Pulling latest changes..."
    git -C "$BOT_DIR" pull origin main 2>/dev/null || log "Warning: git pull failed"
fi

# Step 2: Install/update dependencies
log "Installing dependencies..."
pip3 install -r "$BOT_DIR/requirements.txt" 2>&1 | tail -1

# Step 3: Check .env
if [ ! -f "$BOT_DIR/.env" ]; then
    log "ERROR: .env file not found!"
    exit 1
fi

# Step 4: Stop existing process
log "Stopping existing bot..."
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2

# Step 5: Start bot
log "Starting bot in $MODE mode..."
cd "$BOT_DIR"
nohup python3 main.py > "$BOT_DIR/logs/bot.log" 2>&1 &
BOT_PID=$!
log "Bot started with PID: $BOT_PID"

# Step 6: Health check
sleep 3
if kill -0 $BOT_PID 2>/dev/null; then
    log "Bot is running successfully!"
else
    log "ERROR: Bot failed to start!"
    exit 1
fi

echo ""
echo "Bot deployed successfully!"
echo "Mode: $MODE"
echo "PID: $BOT_PID"
echo "Logs: $BOT_DIR/logs/bot.log"

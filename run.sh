#!/bin/bash
# اسکریپت اجرای بازوی بله

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════╗"
echo "║    🚀 Bale Bot Launcher                 ║"
echo "╚══════════════════════════════════════════╝"

# حالت اجرا
MODE="${1:-polling}"

case "$MODE" in
    polling|poll)
        echo "📡 Mode: Long Polling"
        python3 main.py
        ;;
    webhook)
        PORT="${2:-8443}"
        echo "🌐 Mode: Webhook (port $PORT)"
        python3 webhook_server.py "$PORT"
        ;;
    test)
        echo "🧪 Testing bot connection..."
        python3 -c "
from utils.bale_api import bot
r = bot.get_me()
if r.get('ok'):
    i = r['result']
    print(f'✅ Connected: @{i.get(\"username\")}')
else:
    print(f'❌ Failed: {r.get(\"error\")}')
"
        ;;
    *)
        echo "Usage: ./run.sh [polling|webhook|test] [port]"
        echo ""
        echo "  polling  - Long Polling mode (default)"
        echo "  webhook  - Webhook server mode"
        echo "  test     - Test bot connection"
        ;;
esac

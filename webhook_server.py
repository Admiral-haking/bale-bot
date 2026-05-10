#!/usr/bin/env python3
"""
سرور وب‌هوک اختصاصی برای بازوی بله
می‌توانید این اسکریپت را روی سرور اجرا کنید
"""
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# اضافه کردن مسیر اصلی به PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import logger, BOT_TOKEN
from main import BaleShopBot as BaleBot


class WebhookHandler(BaseHTTPRequestHandler):
    """مدیریت درخواست‌های وب‌هوک"""

    bot_instance = None

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            # پردازش در thread جدا برای پاسخ سریع
            threading.Thread(
                target=self.bot_instance.process_update,
                args=(update,),
                daemon=True
            ).start()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Invalid JSON"}).encode())
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        """بررسی سلامتی سرور"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        html = """<html>
        <head><title>Bale Bot Webhook</title></head>
        <body style="font-family: system-ui; text-align: center; padding: 50px;">
            <h1>🤖 Bale Bot Webhook Server</h1>
            <p>Status: <strong style="color: green;">RUNNING</strong></p>
            <p>Bot is active and processing updates via webhook.</p>
        </body>
        </html>"""
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        logger.debug(f"HTTP: {format % args}")


def main():
    """راه‌اندازی سرور وب‌هوک"""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("❌ توکن بازو معتبر نیست!")
        print("⚠️  لطفاً توکن معتبر را در فایل .env قرار دهید.")
        sys.exit(1)

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8443

    bot_app = BaleBot()
    if not bot_app.check_token():
        sys.exit(1)

    WebhookHandler.bot_instance = bot_app
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)

    print(f"\n🌐 Webhook server running on port {port}")
    print(f"🔗 Webhook URL: http://your-server-ip:{port}")
    print("   (Use https://your-domain.com:{port} for production)")
    print("\n⚠️  Don't forget to set webhook URL in your bot:")
    print(f"   https://tapi.bale.ai/bot<YOUR_TOKEN>/setWebhook?url=https://your-domain.com:{port}")
    print("\n⏸ Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down webhook server...")
        server.shutdown()
        print("✅ Server stopped.")


if __name__ == "__main__":
    main()

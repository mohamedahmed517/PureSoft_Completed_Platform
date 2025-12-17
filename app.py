"""
Afaq Store Bot - Main Application
"""
import requests
import web_database
import auth_database
from config import Config
from datetime import datetime
from utils.logger import logger
from routes.admin import admin_bp
from utils.metrics import metrics
from routes.health import health_bp
from routes.web_chat import web_chat_bp
from routes.metrics import metrics_bp
from flask import Flask, request, jsonify
from services.products import get_product_count
from concurrent.futures import ThreadPoolExecutor
from services.history import conversation_history
from handlers.telegram import process_telegram_message

Config.validate()

app = Flask(__name__)

app.secret_key = Config.SECRET_KEY
app.register_blueprint(health_bp)
app.register_blueprint(metrics_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(web_chat_bp)

executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    """Webhook endpoint for Telegram updates"""
    try:
        update = request.get_json()
        executor.submit(process_telegram_message, update)
        return jsonify(success=True), 200
    except Exception as e:
        logger.error(f"❌ Error in telegram_webhook: {e}", exc_info=True)
        metrics.track_error("webhook")
        return jsonify(success=False, error="Internal error"), 500
        
@app.route("/")
def home():
    """Home page - shows Telegram & Web server status"""
    if not Config.TELEGRAM_TOKEN:
        return """
        <html>
        <head><title>Afaq Store Bot</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🤖 Afaq Store Bot</h1>
            <p style="color: #dc3545;">⚠️ Telegram token not configured</p>
        </body>
        </html>
        """
    try:
        domain = Config.get_webhook_domain(request.host)
        webhook_url = f"https://{domain}/telegram"
        set_result = requests.get(
            f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/setWebhook",
            params={"url": webhook_url},
            timeout=10
        ).json()
       
        webhook_status = "✅ Active" if set_result.get("ok") else "❌ Failed"
        webhook_color = "#28a745" if set_result.get("ok") else "#dc3545"
        info_result = requests.get(
            f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getWebhookInfo",
            timeout=10
        ).json()
        
        pending_updates = info_result.get("result", {}).get("pending_update_count", 0)
        telegram_db_status = '✅ Connected' if Config.TELEGRAM_DATABASE_URL else '❌ Not configured'
        web_db_status = '✅ Connected' if Config.WEB_DATABASE_URL else '❌ Not configured'
        auth_db_status = '✅ Connected' if Config.AUTH_DATABASE_URL else '❌ Not configured'
        web_server_status = "✅ Active"
        web_server_color = "#28a745"
        web_server_url = f"https://{domain}"
        return f"""
        <html>
        <head>
            <title>Afaq Store Bot - Railway</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h3 {{
                    color: #34495e;
                    margin-top: 25px;
                    margin-bottom: 15px;
                }}
                .status {{
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                    border-left: 4px solid;
                }}
                .success {{
                    background-color: #d4edda;
                    border-color: #28a745;
                    color: #155724;
                }}
                .info {{
                    background-color: #d1ecf1;
                    border-color: #17a2b8;
                    color: #0c5460;
                }}
                .server-section {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 25px 0;
                }}
                .server-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border: 2px solid #dee2e6;
                }}
                .server-card.active {{
                    border-color: #28a745;
                    background: #d4edda;
                }}
                .server-card h4 {{
                    margin-top: 0;
                    color: #2c3e50;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .server-icon {{
                    font-size: 24px;
                }}
                a {{
                    color: #007bff;
                    text-decoration: none;
                    font-weight: 500;
                }}
                a:hover {{ text-decoration: underline; }}
                .badge {{
                    display: inline-block;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-left: 10px;
                }}
                .badge-success {{ background: #28a745; color: white; }}
                .badge-info {{ background: #17a2b8; color: white; }}
                .badge-warning {{ background: #ffc107; color: #000; }}
                code {{
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .db-section {{
                    background: #f8f9fa;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                    border-left: 4px solid #6c757d;
                }}
                .db-item {{
                    padding: 8px 0;
                    border-bottom: 1px solid #dee2e6;
                }}
                .db-item:last-child {{
                    border-bottom: none;
                }}
                @media (max-width: 768px) {{
                    .server-section {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Afaq Store Bot <span class="badge badge-success">Online</span></h1>
               
                <div class="status success">
                    <strong>Status:</strong> Bot is running successfully on Railway! 🚀
                </div>
               
                <h3>🌐 Server Status</h3>
                <div class="server-section">
                    <!-- Telegram Server Card -->
                    <div class="server-card {'active' if set_result.get('ok') else ''}">
                        <h4>
                            <span class="server-icon">📱</span>
                            Telegram Server
                            <span class="badge {'badge-success' if set_result.get('ok') else 'badge-warning'}">
                                {'Active' if set_result.get('ok') else 'Inactive'}
                            </span>
                        </h4>
                        <p><strong>Webhook Status:</strong> {webhook_status}</p>
                        <p><strong>Webhook URL:</strong><br><code>{webhook_url}</code></p>
                        <p><strong>Pending Updates:</strong> {pending_updates}</p>
                        <p><strong>Active Conversations:</strong> {len(conversation_history)}</p>
                    </div>
                   
                    <!-- Web Server Card -->
                    <div class="server-card active">
                        <h4>
                            <span class="server-icon">💻</span>
                            Web Server
                            <span class="badge badge-success">Active</span>
                        </h4>
                        <p><strong>Server Status:</strong> {web_server_status}</p>
                        <p><strong>Web URL:</strong><br><code>{web_server_url}</code></p>
                        <p><strong>Status:</strong> Ready to accept web requests</p>
                        <p><strong>Web Interface:</strong> <a href="/chat">💬 Chat Now</a></p>
                    </div>
                </div>
               
                <div class="status info">
                    <strong>📦 Products Loaded:</strong> {get_product_count()} <span class="badge badge-info">CSV</span>
                </div>
               
                <div class="db-section">
                    <h3 style="margin-top: 0;">🗄️ Database Status (3 Separate Databases)</h3>
                    <div class="db-item">
                        <strong>📱 Telegram Database:</strong> {telegram_db_status}
                        <br><small>Stores Telegram conversation history</small>
                    </div>
                    <div class="db-item">
                        <strong>💻 Web Conversations Database:</strong> {web_db_status}
                        <br><small>Stores web chat conversation history</small>
                    </div>
                    <div class="db-item">
                        <strong>🔐 Authentication Database:</strong> {auth_db_status}
                        <br><small>Stores user accounts and login credentials</small>
                    </div>
                </div>
               
                <div style="margin-top: 30px;">
                    <h3>🔗 Quick Links</h3>
                    <p>
                        <a href="/health">🏥 Health Check</a> |
                        <a href="/metrics">📊 Metrics</a> |
                        <a href="/chat">💬 Web Chat</a>
                    </p>
                </div>
               
                <div class="footer">
                    <p>Deployed on <strong>Railway</strong> | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>💡 <strong>Tip:</strong> Check Railway logs for real-time bot activity</p>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"❌ Error setting up webhook: {e}")
        
        return f"""
        <html>
        <head><title>Afaq Store Bot - Error</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>⚠️ Bot Running - Webhook Setup Failed</h1>
            <p style="color: #dc3545;">Error: {str(e)}</p>
            <p><a href="/health">Check Health Status</a></p>
        </body>
        </html>
        """
@app.errorhandler(500)

def internal_error_handler(e):
    """Handle internal server errors"""
    logger.error(f"❌ Internal server error: {e}", exc_info=True)
    return jsonify(error="Internal server error"), 500
    
if __name__ == "__main__":
    logger.info(f"🚀 Starting Afaq Store Bot on Railway (Port: {Config.PORT})")
    logger.info("📊 Databases:")
    logger.info(f" - Telegram DB: {'✅ Configured' if Config.TELEGRAM_DATABASE_URL else '❌ Not configured'}")
    logger.info(f" - Web DB: {'✅ Configured' if Config.WEB_DATABASE_URL else '❌ Not configured'}")
    logger.info(f" - Auth DB: {'✅ Configured' if Config.AUTH_DATABASE_URL else '❌ Not configured'}")
    logger.info("🌐 Servers:")
    logger.info(f" - Telegram Server: ✅ Will be activated on first webhook")
    logger.info(f" - Web Server: ✅ Active on port {Config.PORT}")
    app.run(host="0.0.0.0", port=Config.PORT)

"""
Admin routes
"""
from config import Config
from utils.logger import logger
from flask import jsonify, request, Blueprint
from services.history import cleanup_old_conversations, conversation_history

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin/cleanup", methods=["POST"])
def admin_cleanup():
    """Admin endpoint to cleanup old conversations"""
    auth_token = request.headers.get("Authorization")
    secret = Config.ADMIN_SECRET
    if auth_token != f"Bearer {secret}":
        return jsonify(error="Unauthorized"), 401

    try:
        cleaned = cleanup_old_conversations(days=30)
        logger.info(f"🧹 Cleaned up {cleaned} old conversations")
        
        return jsonify({
            "cleaned": cleaned,
            "remaining": len(conversation_history)
        }), 200

    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
        return jsonify(error=str(e)), 500
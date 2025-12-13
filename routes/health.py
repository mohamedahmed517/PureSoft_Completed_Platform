"""
Health check routes
"""
from config import Config
from datetime import datetime
from flask import jsonify, Blueprint
from services.products import get_product_count
from services.history import conversation_history
from database import get_db_connection, release_db_connection

health_bp = Blueprint('health', __name__)

@health_bp.route("/health")
def health_check():
    """Health check endpoint for Railway"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "not configured",
        "products_loaded": get_product_count(),
        "active_conversations": len(conversation_history),
        "platform": "Railway"
    }

    if Config.DATABASE_URL:
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
                health["database"] = "connected"
            except Exception:
                health["database"] = "error"
                health["status"] = "unhealthy"
            finally:
                release_db_connection(conn)
        else:
            health["database"] = "connection_failed"
            health["status"] = "degraded"
    
    status_code = 200 if health["status"] == "healthy" else 503
    return jsonify(health), status_code
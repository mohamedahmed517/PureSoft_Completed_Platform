"""
Metrics routes
"""
from datetime import datetime
from utils.metrics import metrics
from flask import jsonify, Blueprint
from services.history import conversation_history

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route("/metrics")
def get_metrics_endpoint():
    """Metrics endpoint"""
    stats = metrics.get_stats()
    stats["active_conversations"] = len(conversation_history)
    stats["timestamp"] = datetime.now().isoformat()

    return jsonify(stats)
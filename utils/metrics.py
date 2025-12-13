"""
Metrics tracking for the bot
"""
from collections import Counter

class Metrics:
    """Centralized metrics tracking"""

    def __init__(self):
        self.total_messages = Counter()
        self.errors = Counter()
        self.response_times = []

    def track_message(self, message_type):
        """Track a message"""
        self.total_messages[message_type] += 1

    def track_error(self, error_type):
        """Track an error"""
        self.errors[error_type] += 1

    def track_response_time(self, time_seconds):
        """Track response time"""
        self.response_times.append(time_seconds)
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_stats(self):
        """Get metrics statistics"""
        sorted_times = sorted(self.response_times)
        
        avg_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )

        p50 = sorted_times[len(sorted_times) // 2] if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0

        return {
            "total_messages": dict(self.total_messages),
            "total_errors": dict(self.errors),
            "total_error_count": sum(self.errors.values()),
            "response_times": {
                "avg_seconds": round(avg_time, 3),
                "p50_seconds": round(p50, 3),
                "p95_seconds": round(p95, 3),
                "p99_seconds": round(p99, 3),
                "min_seconds": round(min(sorted_times), 3) if sorted_times else 0,
                "max_seconds": round(max(sorted_times), 3) if sorted_times else 0
            }
        }

metrics = Metrics()
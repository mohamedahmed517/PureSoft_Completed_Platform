"""
Configuration management for Afaq Store Bot
"""
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

class Config:
    """Application configuration"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    PORT = int(os.getenv("PORT", 5000))
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", 200))
    SAVE_INTERVAL = int(os.getenv("SAVE_INTERVAL", 60))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 3))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL", "")
    RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    IMAGE_MAX_SIZE = int(os.getenv("IMAGE_MAX_SIZE", 5 * 1024 * 1024))
    MESSAGE_QUEUE_SIZE = int(os.getenv("MESSAGE_QUEUE_SIZE", 100))
    ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "false").lower() == "true"
    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "change_me_in_production")

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables!")
        logger.info("✅ Configuration validated successfully")

    @classmethod
    def get_webhook_domain(cls, request_host=None):
        """Get the domain for webhook setup"""
        return cls.RAILWAY_PUBLIC_DOMAIN or cls.RAILWAY_STATIC_URL or request_host
"""
Telegram database connection and operations
"""
from psycopg2 import pool
from config import Config
from utils.logger import logger
from psycopg2.extras import Json

telegram_db_pool = None

def init_telegram_db_pool():
    """Initialize Telegram database connection pool"""
    global telegram_db_pool
    
    if not Config.TELEGRAM_DATABASE_URL:
        logger.warning("⚠️  No Telegram database configured")
        return
    
    try:
        telegram_db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=Config.TELEGRAM_DATABASE_URL
        )
        logger.info("✅ Telegram database connection pool created")
    except Exception as e:
        logger.error(f"❌ Failed to create Telegram database pool: {e}")
        telegram_db_pool = None

def get_telegram_db_connection():
    """Get a database connection from the Telegram pool"""
    if telegram_db_pool:
        try:
            return telegram_db_pool.getconn()
        except Exception as e:
            logger.error(f"Error getting Telegram DB connection: {e}")
            return None
    return None

def release_telegram_db_connection(conn):
    """Release a database connection back to the Telegram pool"""
    if telegram_db_pool and conn:
        try:
            telegram_db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error releasing Telegram DB connection: {e}")

def init_telegram_database_tables():
    """Initialize Telegram database tables"""
    if not Config.TELEGRAM_DATABASE_URL:
        logger.info("📝 No Telegram database - using in-memory storage")
        return
    
    conn = get_telegram_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telegram_conversations (
                    user_key TEXT PRIMARY KEY,
                    history JSONB NOT NULL DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_telegram_updated_at 
                ON telegram_conversations(updated_at)
            """)
            
            conn.commit()
        logger.info("✅ Telegram database tables initialized")
    except Exception as e:
        logger.error(f"❌ Telegram database initialization error: {e}")
        conn.rollback()
    finally:
        release_telegram_db_connection(conn)

def save_telegram_conversation_to_db(user_key, history):
    """Save a Telegram conversation to database"""
    if not Config.TELEGRAM_DATABASE_URL:
        return False
    
    conn = get_telegram_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO telegram_conversations (user_key, history, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_key) 
                DO UPDATE SET 
                    history = EXCLUDED.history,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_key, Json(history)))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving Telegram conversation: {e}")
        conn.rollback()
        return False
    finally:
        release_telegram_db_connection(conn)

def load_all_telegram_conversations():
    """Load all Telegram conversations from database"""
    if not Config.TELEGRAM_DATABASE_URL:
        return {}
    
    conn = get_telegram_db_connection()
    if not conn:
        return {}
    
    conversations = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_key, history FROM telegram_conversations")
            rows = cur.fetchall()
            for user_key, hist in rows:
                conversations[user_key] = hist
        logger.info(f"✅ Loaded {len(conversations)} Telegram conversations")
    except Exception as e:
        logger.error(f"❌ Error loading Telegram conversations: {e}")
    finally:
        release_telegram_db_connection(conn)
    
    return conversations

init_telegram_db_pool()
init_telegram_database_tables()

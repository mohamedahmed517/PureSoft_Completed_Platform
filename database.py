"""
Database connection and operations
"""
from psycopg2 import pool
from config import Config
from utils.logger import logger
from psycopg2.extras import Json

db_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    
    if not Config.DATABASE_URL:
        logger.warning("⚠️  No database configured")
        return
    
    try:
        db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=Config.DATABASE_URL
        )
        logger.info("✅ Database connection pool created")
    except Exception as e:
        logger.error(f"❌ Failed to create database pool: {e}")
        db_pool = None

def get_db_connection():
    """Get a database connection from the pool"""
    if db_pool:
        try:
            return db_pool.getconn()
        except Exception as e:
            logger.error(f"Error getting DB connection: {e}")
            return None
    return None

def release_db_connection(conn):
    """Release a database connection back to the pool"""
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error releasing DB connection: {e}")

def init_database_tables():
    """Initialize database tables"""
    if not Config.DATABASE_URL:
        logger.info("📝 No database - using in-memory storage")
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    user_key TEXT PRIMARY KEY,
                    history JSONB NOT NULL DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_updated_at 
                ON conversation_history(updated_at)
            """)
            
            conn.commit()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        conn.rollback()
    finally:
        release_db_connection(conn)

def save_conversation_to_db(user_key, history):
    """Save a single conversation to database"""
    if not Config.DATABASE_URL:
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversation_history (user_key, history, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_key) 
                DO UPDATE SET 
                    history = EXCLUDED.history,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_key, Json(history)))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        conn.rollback()
        return False
    finally:
        release_db_connection(conn)

def load_all_conversations():
    """Load all conversations from database"""
    if not Config.DATABASE_URL:
        return {}
    
    conn = get_db_connection()
    if not conn:
        return {}
    
    conversations = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_key, history FROM conversation_history")
            rows = cur.fetchall()
            for user_key, hist in rows:
                conversations[user_key] = hist
        logger.info(f"✅ Loaded {len(conversations)} conversations from database")
    except Exception as e:
        logger.error(f"❌ Error loading conversations: {e}")
    finally:
        release_db_connection(conn)
    
    return conversations

init_db_pool()
init_database_tables()
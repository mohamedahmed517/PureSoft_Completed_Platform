"""
Web conversations database operations
"""
from psycopg2 import pool
from config import Config
from utils.logger import logger
from psycopg2.extras import Json

web_db_pool = None

def init_web_db_pool():
    """Initialize web database connection pool"""
    global web_db_pool
    
    if not Config.WEB_DATABASE_URL:
        logger.warning("⚠️  No web database configured")
        return
    
    try:
        web_db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=Config.WEB_DATABASE_URL
        )
        logger.info("✅ Web database connection pool created")
    except Exception as e:
        logger.error(f"❌ Failed to create web database pool: {e}")
        web_db_pool = None

def get_web_db_connection():
    """Get a connection from web database pool"""
    if web_db_pool:
        try:
            return web_db_pool.getconn()
        except Exception as e:
            logger.error(f"Error getting web DB connection: {e}")
            return None
    return None

def release_web_db_connection(conn):
    """Release connection back to web database pool"""
    if web_db_pool and conn:
        try:
            web_db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error releasing web DB connection: {e}")

def init_web_database_tables():
    """Initialize web database tables (conversations only)"""
    if not Config.WEB_DATABASE_URL:
        logger.info("📝 No web database configured")
        return
    
    conn = get_web_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS web_conversations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    history JSONB NOT NULL DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_web_conv_user 
                ON web_conversations(user_id)
            """)
            
            conn.commit()
        logger.info("✅ Web database tables initialized")
    except Exception as e:
        logger.error(f"❌ Web database initialization error: {e}")
        conn.rollback()
    finally:
        release_web_db_connection(conn)

def save_web_conversation(user_id, history):
    """Save web user conversation"""
    if not Config.WEB_DATABASE_URL:
        return False
    
    conn = get_web_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO web_conversations (user_id, history, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    history = EXCLUDED.history,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, Json(history)))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving web conversation: {e}")
        conn.rollback()
        return False
    finally:
        release_web_db_connection(conn)

def load_web_conversation(user_id):
    """Load conversation history for a web user"""
    if not Config.WEB_DATABASE_URL:
        return []
    
    conn = get_web_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT history FROM web_conversations 
                WHERE user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            return row[0] if row else []
    except Exception as e:
        logger.error(f"Error loading web conversation: {e}")
        return []
    finally:
        release_web_db_connection(conn)

def clear_web_conversation(user_id):
    """Clear conversation for a web user"""
    if not Config.WEB_DATABASE_URL:
        return False
    
    conn = get_web_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE web_conversations 
                SET history = '[]'::jsonb, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error clearing web conversation: {e}")
        conn.rollback()
        return False
    finally:
        release_web_db_connection(conn)

def load_all_web_conversations():
    """Load all web conversations"""
    if not Config.WEB_DATABASE_URL:
        return {}
    
    conn = get_web_db_connection()
    if not conn:
        return {}
    
    conversations = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, history FROM web_conversations")
            rows = cur.fetchall()
            for user_id, hist in rows:
                conversations[f"web:{user_id}"] = hist
        logger.info(f"✅ Loaded {len(conversations)} web conversations")
    except Exception as e:
        logger.error(f"❌ Error loading web conversations: {e}")
    finally:
        release_web_db_connection(conn)
    
    return conversations

init_web_db_pool()
init_web_database_tables()

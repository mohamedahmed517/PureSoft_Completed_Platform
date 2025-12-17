"""
Authentication database operations (user accounts only)
"""
import bcrypt
from config import Config
from psycopg2 import pool
from utils.logger import logger

auth_db_pool = None

def init_auth_db_pool():
    """Initialize auth database connection pool"""
    global auth_db_pool
    
    if not Config.AUTH_DATABASE_URL:
        logger.warning("⚠️  No auth database configured")
        return
    
    try:
        auth_db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=Config.AUTH_DATABASE_URL
        )
        logger.info("✅ Auth database connection pool created")
    except Exception as e:
        logger.error(f"❌ Failed to create auth database pool: {e}")
        auth_db_pool = None

def get_auth_db_connection():
    """Get a connection from auth database pool"""
    if auth_db_pool:
        try:
            return auth_db_pool.getconn()
        except Exception as e:
            logger.error(f"Error getting auth DB connection: {e}")
            return None
    return None

def release_auth_db_connection(conn):
    """Release connection back to auth database pool"""
    if auth_db_pool and conn:
        try:
            auth_db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error releasing auth DB connection: {e}")

def init_auth_database_tables():
    """Initialize auth database tables (users only)"""
    if not Config.AUTH_DATABASE_URL:
        logger.info("📝 No auth database configured")
        return
    
    conn = get_auth_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_username 
                ON users(username)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_email 
                ON users(email)
            """)
            
            conn.commit()
        logger.info("✅ Auth database tables initialized")
    except Exception as e:
        logger.error(f"❌ Auth database initialization error: {e}")
        conn.rollback()
    finally:
        release_auth_db_connection(conn)

def hash_password(password):
    """Hash a password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def register_user(username, email, password):
    """Register new user"""
    if not Config.AUTH_DATABASE_URL:
        return None, "Auth database not configured"
    
    conn = get_auth_db_connection()
    if not conn:
        return None, "Database connection failed"
    
    try:
        password_hash = hash_password(password)
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING user_id
            """, (username, email, password_hash))
            user_id = cur.fetchone()[0]
        
        conn.commit()
        logger.info(f"✅ New user registered: {username} (ID: {user_id})")
        return user_id, None
        
    except Exception as e:
        conn.rollback()
        error_msg = str(e).lower()
        
        if "unique constraint" in error_msg:
            if "username" in error_msg:
                return None, "Username already exists"
            elif "email" in error_msg:
                return None, "Email already exists"
        
        logger.error(f"❌ Registration error: {e}")
        return None, "Registration failed"
        
    finally:
        release_auth_db_connection(conn)

def authenticate_user(username, password):
    """Authenticate user"""
    if not Config.AUTH_DATABASE_URL:
        return None, "Auth database not configured"
    
    conn = get_auth_db_connection()
    if not conn:
        return None, "Database connection failed"
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, password_hash, is_active 
                FROM users 
                WHERE username = %s
            """, (username,))
            row = cur.fetchone()
        
        if not row:
            return None, "Invalid username or password"
        
        user_id, password_hash, is_active = row
        
        if not is_active:
            return None, "Account is deactivated"
        
        if not verify_password(password, password_hash):
            return None, "Invalid username or password"
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE user_id = %s
            """, (user_id,))
        conn.commit()
        
        logger.info(f"✅ User authenticated: {username} (ID: {user_id})")
        return user_id, None
        
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        return None, "Authentication failed"
        
    finally:
        release_auth_db_connection(conn)

def get_user_info(user_id):
    """Get user information"""
    if not Config.AUTH_DATABASE_URL:
        return None
    
    conn = get_auth_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT username, email, created_at, last_login, is_active
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            row = cur.fetchone()
        
        if row:
            return {
                "user_id": user_id,
                "username": row[0],
                "email": row[1],
                "created_at": row[2],
                "last_login": row[3],
                "is_active": row[4]
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting user info: {e}")
        return None
        
    finally:
        release_auth_db_connection(conn)

def get_user_by_username(username):
    """Get user by username"""
    if not Config.AUTH_DATABASE_URL:
        return None
    
    conn = get_auth_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email 
                FROM users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            row = cur.fetchone()
        
        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "email": row[2]
            }
        return None
        
    finally:
        release_auth_db_connection(conn)

init_auth_db_pool()
init_auth_database_tables()

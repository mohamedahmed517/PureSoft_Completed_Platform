"""
Conversation history management
"""
import time
import threading
from config import Config
from utils.logger import logger
from datetime import datetime, timedelta
from telegram_database import save_telegram_conversation_to_db, load_all_telegram_conversations

conversation_history = {}

def add_message(user_key, role, content, timestamp):
    """Add a message to conversation history"""
    if user_key not in conversation_history:
        conversation_history[user_key] = []
    
    conversation_history[user_key].append({
        "role": role,
        "content": content,
        "timestamp": timestamp
    })
    
    if len(conversation_history[user_key]) > Config.MAX_HISTORY:
        conversation_history[user_key] = conversation_history[user_key][-Config.MAX_HISTORY:]

def get_conversation_context(user_key, max_messages=10):
    """Get conversation context for a user"""
    history = conversation_history.get(user_key, [])
    
    if not history:
        return "لا توجد محادثات سابقة", "لا توجد رسائل سابقة"
    
    recent = history[-max_messages:] if len(history) > max_messages else history
    
    history_text = "\n".join([
        f"{msg['role']}: {msg['content'][:100]}" 
        for msg in recent
    ])
    
    recent_messages = "\n".join([
        f"- {msg['role']}: {msg['content'][:150]}" 
        for msg in recent[-5:]
    ])
    
    return history_text, recent_messages

def clear_conversation(user_key):
    """Clear conversation history for a user"""
    if user_key in conversation_history:
        conversation_history[user_key] = []
        logger.info(f"🗑️  Cleared conversation for {user_key}")
        return True
    return False

def get_conversation_stats(user_key):
    """Get conversation statistics for a user"""
    history = conversation_history.get(user_key, [])
    
    user_messages = [msg for msg in history if msg['role'] == 'user']
    
    return {
        "message_count": len(user_messages),
        "conversation_count": 1 if history else 0,
        "total_messages": len(history)
    }

def cleanup_old_conversations(days=30):
    """Clean up conversations older than specified days"""
    if not conversation_history:
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cleaned_count = 0
    
    for user_key in list(conversation_history.keys()):
        history = conversation_history[user_key]
        if not history:
            continue
        
        try:
            last_msg = history[-1]
            last_time = datetime.strptime(last_msg['timestamp'], "%Y-%m-%d %H:%M")
            
            if last_time < cutoff_date:
                del conversation_history[user_key]
                cleaned_count += 1
                logger.info(f"🧹 Cleaned old conversation for {user_key}")
        except Exception as e:
            logger.warning(f"⚠️  Error checking conversation age: {e}")
            continue
    
    return cleaned_count

def save_all_conversations():
    """Background task to periodically save all conversations"""
    while True:
        time.sleep(Config.SAVE_INTERVAL)

        if not Config.TELEGRAM_DATABASE_URL:
            continue

        try:
            count = 0
            for user_key, hist in list(conversation_history.items()):
                if save_telegram_conversation_to_db(user_key, hist):
                    count += 1
            logger.info(f"💾 Saved {count} conversations to database")
        except Exception as e:
            logger.error(f"❌ Error in save task: {e}")

def init_conversation_history():
    """Load conversation history from database"""
    global conversation_history
    conversations = load_all_telegram_conversations()
    conversation_history.update(conversations)
    logger.info(f"✅ Loaded {len(conversations)} conversation histories")

init_conversation_history()

save_thread = threading.Thread(target=save_all_conversations, daemon=True)
save_thread.start()
logger.info("✅ Background conversation save task started")

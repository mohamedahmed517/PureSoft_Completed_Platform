"""
Conversation history management
"""
import time
import threading
from config import Config
from datetime import datetime
from utils.logger import logger
from collections import defaultdict
from database import save_conversation_to_db, load_all_conversations

conversation_history = defaultdict(list)

def init_conversation_history():
    """Load conversation history from database"""
    global conversation_history
    conversations = load_all_conversations()
    conversation_history.update(conversations)
    logger.info(f"✅ Loaded {len(conversations)} conversation histories")

def save_all_conversations():
    """Background task to periodically save all conversations"""
    while True:
        time.sleep(Config.SAVE_INTERVAL)

        if not Config.DATABASE_URL:
            continue

        try:
            count = 0
            for user_key, hist in list(conversation_history.items()):
                if save_conversation_to_db(user_key, hist):
                    count += 1
            logger.info(f"💾 Saved {count} conversations to database")
        except Exception as e:
            logger.error(f"❌ Error in save task: {e}")

def add_message(user_key, role, text, timestamp=None):
    """Add a message to conversation history"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    conversation_history[user_key].append({
        "role": role,
        "text": text,
        "time": timestamp
    })

    if len(conversation_history[user_key]) > Config.MAX_HISTORY:
        conversation_history[user_key] = conversation_history[user_key][-Config.MAX_HISTORY:]

def get_conversation_context(user_key, limit=10):
    """Get conversation context for prompts"""
    history_text = "\n".join([
        f"{'العميل' if e['role']=='user' else 'البوت'}: {e['text'][:120]}"
        for e in conversation_history[user_key][-limit:]
    ])

    recent_messages = "\n".join([
        e["text"] for e in conversation_history[user_key][-limit:] 
        if "text" in e
    ])

    return history_text, recent_messages

def clear_conversation(user_key):
    """Clear conversation history for a user"""
    if user_key in conversation_history:
        conversation_history[user_key] = []
        return True
    return False

def get_conversation_stats(user_key):
    """Get statistics for a user's conversation"""
    if user_key not in conversation_history:
        return {"message_count": 0, "conversation_count": 0}

    user_messages = [m for m in conversation_history[user_key] if m.get("role") == "user"]

    return {
        "message_count": len(user_messages),
        "conversation_count": len(conversation_history[user_key]) // 2
    }

def cleanup_old_conversations(days=30):
    """Clean up conversations older than specified days"""
    cutoff_timestamp = datetime.now().timestamp() - (days * 24 * 60 * 60)
    cleaned = 0

    for user_key in list(conversation_history.keys()):
        if conversation_history[user_key]:
            last_msg_time = conversation_history[user_key][-1].get("time", "")
            try:
                msg_timestamp = datetime.strptime(last_msg_time, "%Y-%m-%d %H:%M").timestamp()
                if msg_timestamp < cutoff_timestamp:
                    del conversation_history[user_key]
                    cleaned += 1
            except:
                pass

    return cleaned

init_conversation_history()

threading.Thread(target=save_all_conversations, daemon=True).start()
logger.info("✅ Background save thread started")
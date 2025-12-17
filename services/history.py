from telegram_database import save_telegram_conversation_to_db, load_all_telegram_conversations

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


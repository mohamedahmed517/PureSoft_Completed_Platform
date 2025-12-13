"""
Bot command handlers
"""
from utils.logger import logger
from services.gemini import gemini_chat
from services.history import clear_conversation, get_conversation_stats

def handle_command(command, user_key):
    """Handle bot commands"""
    command = command.lower().strip()
    
    if command == "/start":
        return "أهلاً وسهلاً! أنا البوت الذكي بتاع آفاق ستورز 👋\nابعتلي أي سؤال عن المنتجات أو صورة وأنا هساعدك!"
    
    elif command in ["/clear", "/reset"]:
        if clear_conversation(user_key):
            return "تمام، مسحت المحادثة القديمة. ابدأ من جديد! 🔄"
        return "مفيش محادثات عشان امسحها"
    
    elif command == "/help":
        return """أنا هنا عشان أساعدك تلاقي أحسن المنتجات! 💫

ممكن تعمل:
- تسألني عن منتجات معينة
- تبعتلي صورة وأحللها
- تبعتلي صوت وأرد عليك
- اكتب /clear عشان تمسح المحادثة
- اكتب /stats عشان تشوف إحصائياتك"""
    
    elif command == "/stats":
        stats = get_conversation_stats(user_key)
        return f"""📊 إحصائياتك:
- عدد رسائلك: {stats['message_count']}
- عدد المحادثات: {stats['conversation_count']}"""
    
    else:
        logger.info(f"📝 Unknown command, treating as text: {command}")
        return gemini_chat(command, user_key=user_key)
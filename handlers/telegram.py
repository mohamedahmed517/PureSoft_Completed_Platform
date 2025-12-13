"""
Telegram message handlers
"""
import base64
import requests
from config import Config
from utils.logger import logger
from utils.metrics import metrics
from services.gemini import gemini_chat
from handlers.commands import handle_command

def download_telegram_file(file_id, file_type="photo"):
    """Download a file from Telegram servers"""
    try:
        file_info = requests.get(
            f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=Config.REQUEST_TIMEOUT
        ).json()

        if not file_info.get("ok"):
            logger.error(f"Failed to get {file_type} file info")
            return None

        file_size = file_info["result"].get("file_size", 0)
        if file_size > Config.IMAGE_MAX_SIZE:
            logger.warning(f"⚠️  File too large: {file_size} bytes")
            return None

        path = file_info["result"]["file_path"]
        url = f"https://api.telegram.org/file/bot{Config.TELEGRAM_TOKEN}/{path}"

        response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()

        logger.info(f"✅ Downloaded {file_type} ({file_size} bytes)")
        return response.content

    except requests.Timeout:
        logger.error(f"⏱️ Timeout downloading {file_type}")
        return None
    except Exception as e:
        logger.error(f"❌ Error downloading {file_type}: {e}")
        return None

def send_telegram_message(chat_id, text):
    """Send a message via Telegram bot"""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"❌ Error sending Telegram message: {e}")
        return False

def validate_telegram_update(update):
    """Validate incoming Telegram update"""
    if not update or not isinstance(update, dict):
        return False

    if "message" not in update:
        return False

    msg = update["message"]
    required_fields = ["chat", "from"]
    
    return all(field in msg for field in required_fields)

def process_telegram_message(update):
    """Process a Telegram message (runs in background thread)"""
    try:
        if not validate_telegram_update(update):
            logger.warning("⚠️  Invalid Telegram update received")
            return

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        user_id = str(msg["from"]["id"])
        user_key = f"telegram:{user_id}"
        
        reply = None

        if "text" in msg:
            text = msg["text"].strip()

            if text.startswith("/"):
                reply = handle_command(text, user_key)
            else:
                logger.info(f"📝 Processing text from {user_key}")
                reply = gemini_chat(text, user_key=user_key)

        elif "photo" in msg:
            logger.info(f"🖼️  Processing photo from {user_key}")
            file_id = msg["photo"][-1]["file_id"]
            img_data = download_telegram_file(file_id, "photo")
            
            if img_data:
                b64 = base64.b64encode(img_data).decode()
                reply = gemini_chat("بعت صورة", image_b64=b64, user_key=user_key)
            else:
                reply = "مش قادر أشوف الصورة دلوقتي، ممكن تبعتها تاني؟"

        elif "voice" in msg or "audio" in msg:
            logger.info(f"🎤 Processing audio from {user_key}")
            voice = msg.get("voice") or msg.get("audio")
            file_id = voice["file_id"]
            audio_bytes = download_telegram_file(file_id, "audio")

            if audio_bytes:
                try:
                    reply = gemini_chat("بعت صوت", audio_data=audio_bytes, user_key=user_key)
                except Exception as e:
                    logger.error(f"❌ Error processing audio: {e}")
                    reply = "الصوت مش واضح، ممكن تبعته تاني؟"
            else:
                reply = "مش قادر أسمع الصوت دلوقتي"

        else:
            reply = "ابعت نص أو صورة أو صوت وأنا هساعدك"

        if reply:
            send_telegram_message(chat_id, reply)
            metrics.track_message("sent")

    except Exception as e:
        logger.error(f"❌ Error processing Telegram message: {e}", exc_info=True)
        metrics.track_error("telegram_processing")
"""
Gemini AI chat service
"""
import io
import time
import base64
from PIL import Image
from models import MODEL
from datetime import datetime
from utils.logger import logger
from utils.metrics import metrics
from services.products import build_product_catalog
from services.history import conversation_history, get_conversation_context, add_message

def gemini_chat(text="", image_b64=None, audio_data=None, user_key="unknown"):
    """Main chat function with Gemini AI"""
    start_time = time.time()
    max_retries = 2

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if len(conversation_history[user_key]) == 0:
            reply = "أهلاً وسهلاً! أنا البوت الذكي بتاع آفاق ستورز\nإزيك؟ تحب أساعدك في إيه النهاردة؟"
            add_message(user_key, "assistant", reply, now)
            metrics.track_message("welcome")
            return reply

        history_text, recent_messages = get_conversation_context(user_key)
        products_text = build_product_catalog()

        prompt = f"""
أنت البوت الذكي بتاع آفاق ستورز، بتتكلم عامية مصرية ودودة، بتحب الموضة والعناية الشخصية وب تعرف تحلل الصور كويس.

آخر محادثة:
{history_text}

دول كل المنتجات اللي موجودة عندنا دلوقتي (خد بالك من الأسماء دي بالحرف لأن اللينكات مربوطة بيها):
{products_text}

آخر رسايل المحادثة:
{recent_messages}

العميل بيقول دلوقتي: {text or "بعت صورة" if not audio_data else "بعت صوت"}

## لو طلب لبس أو عناية أو بعت صورة لبس أو منتج:
- رشحله من المنتجات اللي فوق بالشكل ده بالظبط (سطر للاسم، سطر للسعر، سطر للينك):

تيشيرت قطن سادة ابيض
السعر: 130 جنيه
اللينك: https://afaq-stores.com/product-details/1019

سكارف كشمير طويل
السعر: 290 جنيه
اللينك: https://afaq-stores.com/product-details/1014

جاكيت جلد اسود تقيل مبطن فرو
السعر: 720 جنيه
اللينك: https://afaq-stores.com/product-details/1001

**مهم جدًا:** استخدم أسماء المنتجات زي ما هي مكتوبة فوق من غير ما تقصرها أو تغير فيها ولا حرف.

## لو سأل عن حاجة عامة (مناطق، سياحة، نصايح، أكل، أخبار، طقس، معلومات عامة، أي حاجة تانية):
- رد عليه بشكل طبيعي وودود
- اديله معلومات مفيدة ودقيقة
- لو محتاج تدور على معلومات حديثة استخدم البحث
- متنساش إنك صديق مصري بيساعده مش مجرد بوت متخصص في لبس بس
- لو السؤال مالوش علاقة بالمنتجات خالص متحاولش تفرض عليه منتجات

## لو بعت صورة عادية (مش لبس أو منتج):
- حلل الصورة وقول اللي فيها
- لو صورة مكان أو منطقة → اتكلم عنها وقول معلومات عنها
- لو صورة شخصية أو حاجة عامة → رد عليه بشكل لطيف
- متحاولش ترشح منتجات إلا لو الصورة فيها لبس أو متعلقة بالموضة

## لو بعت صوت:
- اسمع الصوت كويس ورد على اللي بيقوله سواء كان عن منتجات أو أي حاجة تانية

## قواعد عامة:
- لو في صورة → ابدأ الرد بـ "ثانية بس أشوف الصورة..."
- رد بالعامية المصرية 100%
- متحطش إيموجي خالص
- متقولش إنك بوت أبدًا
- كن صديق حقيقي بيساعد في كل حاجة مش بس المنتجات
- لو مش متأكد من معلومة قول كده بصراحة
""".strip()
        response = None
        for attempt in range(max_retries):
            try:
                if audio_data:
                    audio_io = io.BytesIO(audio_data)
                    audio_io.name = "voice.ogg"
                    response = MODEL.generate_content([prompt, audio_io], stream=False)
                    metrics.track_message("with_audio")
                elif image_b64:
                    img = Image.open(io.BytesIO(base64.b64decode(image_b64)))
                    response = MODEL.generate_content([prompt, img], stream=False)
                    metrics.track_message("with_image")
                else:
                    response = MODEL.generate_content(prompt, stream=False)
                    metrics.track_message("text_only")
                break
            except Exception as e:
                logger.warning(f"⚠️  Gemini API attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        
        reply = response.text.strip() if response and hasattr(response, "text") and response.text else "ثواني بس فيه مشكلة دلوقتي..."

        add_message(user_key, "user", text or ("[صورة]" if image_b64 else "[صوت]"), now)
        add_message(user_key, "assistant", reply, now)

        response_time = time.time() - start_time
        metrics.track_response_time(response_time)
        
        logger.info(f"✅ Response generated for {user_key} in {response_time:.2f}s")
        return reply

    except Exception as e:
        logger.error(f"❌ Error in gemini_chat: {e}", exc_info=True)
        metrics.track_error("gemini_chat")

        return "ثواني بس فيه مشكلة دلوقتي هحلها وارجعلك..."


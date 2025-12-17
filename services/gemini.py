"""
Gemini AI chat service
"""
import io
import time
import base64
from PIL import Image
from datetime import datetime
from utils.logger import logger
from utils.metrics import metrics
from services.products import build_product_catalog
from models import CLIENT, GENERATION_CONFIG, SAFETY_SETTINGS
from google.genai import types
from services.history import conversation_history, get_conversation_context, add_message

def gemini_chat(text="", image_b64=None, audio_data=None, user_key="unknown"):
    """Main chat function with Gemini AI"""
    start_time = time.time()
    max_retries = 2
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_text, recent_messages = get_conversation_context(user_key)
        products_text = build_product_catalog()
        prompt = f"""
أنت البوت الذكي بتاع آفاق ستورز، بتتكلم عامية مصرية ودودة وطبيعية.
أنت مساعد شامل بتعرف تتكلم في أي موضوع: موضة، سياحة، طقس، أماكن خروج، نصايح عامة، وأي حاجة تانية.
آخر محادثة:
{history_text}
دول كل المنتجات اللي موجودة عندنا دلوقتي (خد بالك من الأسماء دي بالحرف لأن اللينكات مربوطة بيها):
{products_text}
آخر رسايل المحادثة:
{recent_messages}
العميل بيقول دلوقتي: {text or "بعت صورة" if not audio_data else "بعت صوت"}
قواعد الرد:
1. لو العميل سألك عن حاجة عامة (سياحة، طقس، أماكن، نصايح، أي موضوع) → رد عليه عادي وطبيعي من غير ما ترشح منتجات إلا لو هو طلب كده بوضوح
2. لو سأل عن الطقس في مكان معين → قوله الطقس إيه وممكن تنصحه باللبس المناسب للجو ده (بس مترشحش منتجات إلا لو هو طلب)
3. لو سأل عن أماكن خروج أو فسح → رشحله أماكن حلوة واديله معلومات مفيدة
4. لو قالك "مترشحليش منتجات دلوقتي" أو "مش عايز أشوف منتجات" → مترشحش خالص واتكلم عادي
5. لو طلب منك صراحة يشوف لبس أو منتجات أو بعت صورة لبس/منتج عشان يعرف شبهه إيه:
   - رشحله من المنتجات اللي فوق بالشكل ده بالظبط (سطر للاسم، سطر للسعر، سطر للكاتيجوري، سطر للينك):
  
   تيشيرت قطن سادة ابيض
   السعر: 130 جنيه
   الكاتيجوري: لبس صيفي
   اللينك: https://afaq-stores.com/product-details/1019
  
   سكارف كشمير طويل
   السعر: 290 جنيه
   الكاتيجوري: لبس خريفي
   اللينك: https://afaq-stores.com/product-details/1014
  
   جاكيت جلد اسود تقيل مبطن فرو
   السعر: 720 جنيه
   الكاتيجوري: لبس شتوي
   اللينك: https://afaq-stores.com/product-details/1001
6. مهم جدًا: استخدم أسماء المنتجات زي ما هي مكتوبة فوق من غير ما تقصرها أو تغير فيها ولا حرف
7. لو بعت صورة لبس/منتج → ابدأ الرد بـ "ثانية بس أشوف الصورة..."
8. لو بعت صورة عادية (مش لبس) → حلل الصورة ورد عليه عادي من غير ما ترشح منتجات
9. لو بعت صوت → اسمع الصوت كويس ورد على اللي بيقوله
أسلوب الكلام:
- اتكلم عامية مصرية 100% وبشكل طبيعي ومريح
- متحطش إيموجي خالص
- متقولش إنك بوت أبدًا
- كن مفيد وودود في أي موضوع
- لو مش عارف حاجة، اعترف بكده بشكل طبيعي
رد دلوقتي:
""".strip()
        response = None
        for attempt in range(max_retries):
            try:
                if audio_data:
                    response = CLIENT.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            prompt,
                            {"mime_type": "audio/ogg", "data": audio_data}
                        ],
                        config=types.GenerateContentConfig(
                            **GENERATION_CONFIG,
                            safety_settings=SAFETY_SETTINGS
                        )
                    )
                    metrics.track_message("with_audio")
                   
                elif image_b64:
                    img = Image.open(io.BytesIO(base64.b64decode(image_b64)))
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                   
                    response = CLIENT.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            prompt,
                            {"mime_type": "image/png", "data": img_bytes.read()}
                        ],
                        config=types.GenerateContentConfig(
                            **GENERATION_CONFIG,
                            safety_settings=SAFETY_SETTINGS
                        )
                    )
                    metrics.track_message("with_image")
                   
                else:
                    response = CLIENT.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            **GENERATION_CONFIG,
                            safety_settings=SAFETY_SETTINGS
                        )
                    )
                    metrics.track_message("text_only")
                   
                break
               
            except Exception as e:
                logger.warning(f"⚠️ Gemini API attempt {attempt + 1}/{max_retries} failed: {e}")
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

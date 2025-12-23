"""
Gemini AI chat service
"""
import io
import time
import base64
from PIL import Image
from datetime import datetime
from google.genai import types
from utils.logger import logger
from utils.metrics import metrics
from web_database import save_web_conversation
from services.products import build_product_catalog
from models import CLIENT, GENERATION_CONFIG, SAFETY_SETTINGS
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
أنت مساعد شامل بتعرف تتكلم في أي موضوع.

آخر محادثة:
{history_text}

**بيانات المنتجات - تنسيق جديد هام:**
المنتجات تأتي بالشكل ده: `ID,السعر,اسم_المنتج,الفئة`
مثال: `13,260,هيد اند شولدرز شامبو انتعاش الليمون 400 مل,شامبو`
لما تشوف المنتجات في `{products_text}`، هتعامل معاها كالتالي:
1. كل سطر فيه بيانات منتج كاملة
2. اللينك يتعمل من الـ ID: https://afaq-stores.com/product-details/[ID]

دول المنتجات اللي عندنا دلوقتي:
{products_text}

آخر رسايل المحادثة:
{recent_messages}

العميل بيقول دلوقتي: {text or "بعت صورة" if not audio_data else "بعت صوت"}

**قواعد الرد الأساسية:**

1. **اسمع كويس لآخر رسالة** ورد عليها بشكل طبيعي وعامية مصرية.

2. **لما العميل يذكر كلمة من الكلمات المفتاحية**، ابدأ بالرد عادي وبعدين قول: "بالنسبة لـ [الموضوع]، عندنا حاجات كويسة ممكن تفيدك:" 
   واعرض 2-6 منتجات **من أي فئة تناسب الموقف** - مش شرط لبس! ممكن تكون:
   - منتجات عناية شخصية
   - إكسسوارات
   - أدوات منزلية
   - شنط وحقائب
   - أي منتج ثاني موجود في القائمة

3. **طريقة عرض المنتج - تنسيق إجباري:**
   لكل منتج تعرضه، استخدم **هذا الشكل بالضبط**:
   
   اسم المنتج (من العمود الثالث في الداتا)
   السعر: [السعر من العمود الثاني] جنيه
   الكاتيجوري: [الفئة من العمود الرابع]
   اللينك: https://afaq-stores.com/product-details/[ID من العمود الأول]
   
   سطر فاضي بعد كل منتج.

4. **مثال عملي:** 
   العميل: "عندي حفلة بكرة"
   الرد: "أهلاً يا فندم! حفلة كويسة إن شاء الله. بالنسبة لـ الحفلة، عندنا حاجات كويسة ممكن تفيدك:
   
   انجل برفان لفز 50 مل
   السعر: 115.5 جنيه
   الكاتيجوري: برفان
   اللينك: https://afaq-stores.com/product-details/153
   
   كوتشي ابيض كلاسيك نضيف
   السعر: 380.0 جنيه
   الكاتيجوري: لبس ربيعي
   اللينك: https://afaq-stores.com/product-details/1018"

5. **الكلمات المفتاحية اللي تبدأ بيها الاقتراحات:**
   - برد/شتا/جو بارد/مطر → حاجات للشتا
   - حر/صيف/شمس/جو حار → حاجات للصيف
   - خروجات/فسح/نزهة → حاجات للخروجات
   - هدية/عيد ميلاد/تخرج/مناسبة → حاجات تصلح هدايا
   - سفر/رحلة/أجازة → حاجات للسفر
   - شغل/مكتب/وظيفة → حاجات للشغل
   - رياضة/جيم/تمرين → حاجات رياضية
   - بيت/منزل/ديكور → حاجات للبيت
   
   **مهم:** ماتقترحش منتجات إلا لو جت الكلمة دي في كلام العميل.

6. **الطقس:** لو سأل عن طقس مكان، قوله إيه الأحوال، وانصحه باللبس المناسب، وبعدين اقترح حاجات **أي منتجات** تناسب الجو ده.

7. **لا تتوقف أبداً:** لو لقيت منتج مش كامل، سيبيه وروح لللي بعده. ماتوقفش الرد علشان أي مشكلة في منتج واحد.

8. **ممنوعات:**
   - مترشحش منتجات لو قال "مش عايز" أو "مترشحليش"
   - ماتستعملش إيموجي
   - متقولش إنك بوت/آلي/برنامج

**أسلوبك:**
- ردي بطبيعية زيك، كأنك صاحب المحل.
- ساعد في أي حاجة عامة براحة.
- آخر جملة في الرد: "تحب أساعدك في أي حاجة تانية؟"

رد دلوقتي:
""".strip()
        response = None
        for attempt in range(max_retries):
            try:
                config_dict = GENERATION_CONFIG.model_dump() if hasattr(GENERATION_CONFIG, 'model_dump') else GENERATION_CONFIG.dict()
                config_dict.pop('safety_settings', None)
                
                if audio_data:
                    response = CLIENT.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            prompt,
                            {"mime_type": "audio/ogg", "data": audio_data}
                        ],
                        config=types.GenerateContentConfig(
                            **config_dict,
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
                            **config_dict,
                            safety_settings=SAFETY_SETTINGS
                        )
                    )
                    metrics.track_message("with_image")
                   
                else:
                    response = CLIENT.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            **config_dict,
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
        
        if user_key.startswith("web:"):
            try:
                user_id = int(user_key.split(":")[1])
                history = conversation_history.get(user_key, [])
                save_web_conversation(user_id, history)
                logger.info(f"💾 Saved web conversation for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Error saving web conversation: {e}")
        
        response_time = time.time() - start_time
        metrics.track_response_time(response_time)
       
        logger.info(f"✅ Response generated for {user_key} in {response_time:.2f}s")
        return reply
    except Exception as e:
        logger.error(f"❌ Error in gemini_chat: {e}", exc_info=True)
        metrics.track_error("gemini_chat")
        return "ثواني بس فيه مشكلة دلوقتي هحلها وارجعلك..."

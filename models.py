"""
AI model initialization and configuration
"""
import time
from config import Config
from utils.logger import logger
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def init_gemini_model():
    """Initialize Gemini model with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config={
                    "temperature": 0.9, 
                    "max_output_tokens": 2048
                },
                safety_settings=[
                    {"category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH},
                    {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH},
                    {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH},
                    {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH},
                ]
            )
            logger.info("✅ Gemini AI configured successfully")
            return model
        except Exception as e:
            logger.error(f"❌ Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

MODEL = init_gemini_model()
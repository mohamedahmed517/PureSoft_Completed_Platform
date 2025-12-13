"""
Product catalog management
"""
import os
import pandas as pd
from functools import lru_cache
from utils.logger import logger

@lru_cache(maxsize=1)
def load_products():
    """Load and cache product data from CSV"""
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(BASE_DIR, 'products.csv')
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Loaded {len(df)} products from CSV")
        return df
    except Exception as e:
        logger.error(f"❌ Error loading products CSV: {e}")
        return pd.DataFrame()

def build_product_catalog():
    """Build formatted product catalog for prompts"""
    CSV_DATA = load_products()
    products_text = "المنتجات المتاحة (ممنوع تغيير ولا حرف في الاسم أبدًا):\n"

    for _, row in CSV_DATA.iterrows():
        try:
            name = str(row['product_name_ar']).strip()
            price = float(row['sell_price'])
            cat = str(row['category']).strip()
            pid = str(row['product_id'])
            products_text += f"• {name} | السعر: {price} جنيه | الكاتيجوري: {cat} | اللينك: https://afaq-stores.com/product-details/{pid}\n"
        except Exception as e:
            logger.warning(f"⚠️  Error processing product row: {e}")
            continue

    return products_text

def get_product_count():
    """Get total number of products"""
    return len(load_products())
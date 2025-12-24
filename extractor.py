# extractor.py - UPDATED VERSION with AvalAI + New Fields
import os
import json
import logging
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ✅ اتصال به AvalAI
client = OpenAI(
    api_key=os.getenv("AVALAIGPT_API_KEY"),
    base_url="https://api.avalai.ir/v1",
    timeout=15.0
)

# ✅ پرامپت بهینه‌شده با فیلدهای جدید
EXTRACTOR_SYSTEM_ROLE = "You are a Persian real estate data extractor. Extract data and return ONLY valid JSON."

EXTRACTOR_PROMPT_TEMPLATE = """Extract from this text:
"{text}"

Return JSON (null if missing):
{{"transaction_type": "فروش/رهن و اجاره/پیش‌فروش", 
"property_type": "آپارتمان/ویلا/زمین/مغازه",
"usage_type": "مسکونی/تجاری/اداری",
"price_total": number, "rent": number, "deposit": number, 
"area": number, "bedroom_count": number, 
"build_year": number, "floor": number, 
"total_floors": number, "unit_count": number,
"has_parking": bool, "parking_count": number, 
"has_elevator": bool, "has_storage": bool, 
"storage_count": number, "owner_name": "string", 
"owner_phone": "string", "neighborhood": "string", 
"city": "string"}}"""

def extract_json(text: str) -> Dict:
    """Extract property data from text using LLM"""
    prompt = EXTRACTOR_PROMPT_TEMPLATE.replace("{text}", text[:500])
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=600  # ✅ افزایش برای فیلدهای بیشتر
        )
        
        result = response.choices[0].message.content.strip()
        
        # ✅ Handle markdown safely
        marker = chr(96) * 3
        if result.startswith(marker):
            lines = result.split("\n")
            clean = [line for line in lines if not line.strip().startswith(marker)]
            result = "\n".join(clean)
        
        data = json.loads(result)
        logger.info(f"✅ Extracted from AvalAI: {list(data.keys())}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode failed: {e}")
        return {}
    except TimeoutError:
        logger.error("❌ AvalAI request timed out after 15s")
        return {}
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        return {}

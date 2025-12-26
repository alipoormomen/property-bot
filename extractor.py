# extractor.py - COMPLETE VERSION (FIXED)
import os
import json
import logging
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# اتصال به AvalAI
client = OpenAI(
    api_key=os.getenv("AVALAIGPT_API_KEY"),
    base_url="https://api.avalai.ir/v1",
    timeout=15.0
)

# پرامپت اصلی استخراج اطلاعات ملک
EXTRACTOR_SYSTEM_ROLE = "You are a Persian real estate data extractor. Extract data and return ONLY valid JSON."

EXTRACTOR_PROMPT_TEMPLATE = """Extract real estate info from Persian text:
"{text}"

Return ONLY valid JSON with these fields (use null if not found):
{{
  "transaction_type": "فروش" or "رهن و اجاره" or "پیش‌فروش",
  "property_type": "آپارتمان" or "ویلا" or "زمین" or "مغازه",
  "usage_type": "مسکونی" or "تجاری" or "اداری",
  "area": number (متراژ),
  "bedroom_count": number (تعداد اتاق/خواب),
  "total_floors": number (تعداد کل طبقات ساختمان),
  "floor": number (واحد در طبقه چندم است),
  "unit_count": number (هر طبقه چند واحد دارد),
  "has_elevator": boolean (آسانسور),
  "build_year": number (سال ساخت),
  "price_total": number (قیمت کل یا رهن),
  "rent": number (اجاره ماهیانه),
  "deposit": number (ودیعه),
  "neighborhood": "string" (محله),
  "city": "string" (شهر),
  "owner_name": "string" (نام مالک),
  "owner_phone": "string" (شماره تلفن),
  "has_parking": boolean,
  "has_storage": boolean,
  "additional_features": "string" (امکانات مثل: لابی، استخر، سونا، نگهبان)
}}

IMPORTANT: 
- "واحد در طبقه: 3" means unit_count=3 (3 units per floor)
- "طبقه: 8" or "واحد در طبقه 8" means floor=8
- "امکانات: سونا" means additional_features="سونا"
"""



# پرامپت استخراج امکانات اضافی
FEATURES_SYSTEM_ROLE = "You are a Persian real estate feature extractor. Extract amenities and return ONLY valid JSON."

FEATURES_PROMPT_TEMPLATE = """Extract amenities from this Persian text:
"{text}"

Return JSON with these fields (true/false or null if not mentioned):
{{
  "has_lobby": bool,
  "has_pool": bool,
  "has_sauna": bool,
  "has_gym": bool,
  "has_guard": bool,
  "has_central_vacuum": bool,
  "has_balcony": bool,
  "has_terrace": bool,
  "has_roof_garden": bool,
  "has_video_intercom": bool,
  "has_central_antenna": bool,
  "view_type": "string or null",
  "floor_material": "string or null",
  "cabinet_type": "string or null",
  "cooling_system": "string or null",
  "heating_system": "string or null",
  "additional_features": ["list of other features not in above fields"]
}}"""

# کاراکتر بک‌تیک برای حذف markdown
BACKTICK = chr(96)
TRIPLE_BACKTICK = BACKTICK * 3


def clean_markdown_response(text: str) -> str:
    """حذف markdown code blocks از پاسخ LLM"""
    if text.startswith(TRIPLE_BACKTICK):
        lines = text.split("\n")
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith(TRIPLE_BACKTICK) and stripped != "json":
                clean_lines.append(line)
        return "\n".join(clean_lines)
    return text


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
            max_tokens=600
        )

        result = response.choices[0].message.content.strip()
        result = clean_markdown_response(result)

        data = json.loads(result)

        # حذف مقادیر null
        cleaned = {k: v for k, v in data.items() if v is not None}
        logger.info(f"Extracted fields: {list(cleaned.keys())}")
        return cleaned

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed: {e}")
        return {}
    except TimeoutError:
        logger.error("AvalAI request timed out after 15s")
        return {}
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {}


def extract_additional_features(text: str) -> Dict:
    """Extract additional amenities from free text using LLM"""
    
    # اگر کاربر گفت ندارد
    clean_text = text.strip().lower()
    if clean_text in ["ندارد", "نداره", "خیر", "نه", "no", "none", "-"]:
        return {}

    prompt = FEATURES_PROMPT_TEMPLATE.replace("{text}", text[:500])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": FEATURES_SYSTEM_ROLE},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()
        result = clean_markdown_response(result)

        data = json.loads(result)

        # حذف مقادیر null و false و خالی
        cleaned = {}
        for k, v in data.items():
            if v is not None and v is not False:
                if isinstance(v, list) and len(v) == 0:
                    continue
                if isinstance(v, str) and v == "":
                    continue
                cleaned[k] = v

        logger.info(f"Extracted additional features: {list(cleaned.keys())}")
        return cleaned

    except json.JSONDecodeError as e:
        logger.error(f"Features JSON decode failed: {e}")
        return {"additional_features": [text.strip()]}
    except TimeoutError:
        logger.error("Features request timed out")
        return {"additional_features": [text.strip()]}
    except Exception as e:
        logger.error(f"Features extraction failed: {e}")
        return {"additional_features": [text.strip()]}

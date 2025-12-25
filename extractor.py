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

import logging
from typing import Dict, Any

from extractor import extract_json
from conversation_state import merge_state
from rule_engine import run_rule_engine
from utils import normalize_price, validate_area, validate_year
from services.inference_service import infer_property_type, infer_usage_type, normalize_location
from phone_utils import normalize_iran_phone, validate_phone

logger = logging.getLogger(__name__)

# ✅ متغیرهای message به صورت inline
MSG_UNKNOWN = "متوجه نشدم، لطفاً مجدد تلاش کنید."
MSG_SUMMARY_HEADER = "📋 خلاصه اطلاعات ملک:"
LBL_TRANSACTION = "نوع معامله"
LBL_PROPERTY = "نوع ملک"
LBL_PRICE = "قیمت کل"
LBL_RENT = "اجاره"
LBL_AREA = "متراژ"
LBL_BEDROOM = "تعداد خواب"
LBL_YEAR = "سال ساخت"
LBL_FLOOR = "طبقه"
LBL_TOTAL_FLOORS = "تعداد کل طبقات"
LBL_UNIT_COUNT = "تعداد واحد"
LBL_PHONE = "تلفن مالک"
LBL_NEIGHBORHOOD = "محله"

def process_user_input(text: str, user_id: int) -> str:
    # 1. Extract Raw Data
    extracted = extract_json(text)

    # 2. Validation & Normalization
    if extracted.get("owner_phone"):
        p = normalize_iran_phone(extracted["owner_phone"])
        if validate_phone(p):
            extracted["owner_phone"] = p
        else:
            extracted["owner_phone"] = None

    if extracted.get("build_year"):
        if not validate_year(extracted["build_year"]):
             extracted["build_year"] = None

    for field in ["price_total", "rent"]:
        if extracted.get(field):
            extracted[field] = normalize_price(extracted[field])

    # 3. Merge State
    data = merge_state(user_id, extracted)

    # 4. Inference Layer
    data = infer_property_type(data)
    data = infer_usage_type(data)
    data = normalize_location(data)

    data = merge_state(user_id, data)

    # 5. Rule Engine
    result = run_rule_engine(data)

    # 6. Response Decision
    if result["status"] == "question":
        return result["question"]

    elif result["status"] == "completed":
        return format_summary(data)

    return MSG_UNKNOWN

def format_summary(data: Dict[str, Any]) -> str:
    lines = [MSG_SUMMARY_HEADER]

    keys_map = {
        "transaction_type": LBL_TRANSACTION,
        "property_type": LBL_PROPERTY,
        "price_total": LBL_PRICE,
        "rent": LBL_RENT,
        "area": LBL_AREA,
        "bedroom_count": LBL_BEDROOM,
        "build_year": LBL_YEAR,
        "floor": LBL_FLOOR,
        "total_floors": LBL_TOTAL_FLOORS,
        "unit_count": LBL_UNIT_COUNT,
        "owner_phone": LBL_PHONE,
        "neighborhood": LBL_NEIGHBORHOOD
    }

    for key, label in keys_map.items():
        val = data.get(key)
        if val is not None:
            if key in ["price_total", "rent"] and isinstance(val, (int, float)):
                val = f"{val:,.0f}"
            lines.append(f"{label}: {val}")

    # ✅ استفاده از chr(10) به جای backslash-n
    NEWLINE = chr(10)
    return NEWLINE.join(lines)

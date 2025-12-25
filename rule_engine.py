# rule_engine.py
"""Rule Engine for Property Data Collection"""

import logging
from typing import Dict, Any
from conversation_state import set_pending_field

logger = logging.getLogger(__name__)

# ترتیب فیلدها
FIELD_ORDER = [
    "transaction_type",
    "property_type",
    "area",
    "bedroom_count",
    "total_floors",
    "floor",
    "unit_count",
    "has_elevator",
    "build_year",
    "neighborhood",
    "owner_name",
    "owner_phone",
    "price_total",
    "additional_features",  # آخرین فیلد
]

# فیلدهای اجباری برای هر نوع ملک
REQUIRED_FIELDS_BASE = [
    "transaction_type",
    "property_type", 
    "area",
    "neighborhood",
    "owner_name",
    "owner_phone",
]

# فیلدهای اضافی برای آپارتمان
APARTMENT_FIELDS = [
    "bedroom_count",
    "total_floors",
    "floor",
    "unit_count",
    "has_elevator",
    "build_year",
]

# فیلدهای اختیاری (نباید لوپ بزنند)
OPTIONAL_FIELDS = ["additional_features", "description", "city"]

# سوالات هر فیلد
FIELD_QUESTIONS = {
    "transaction_type": "🏷 قصد چه کاری دارید؟ (فروش / رهن و اجاره)",
    "property_type": "🏠 نوع ملک چیست؟ (آپارتمان، ویلا، زمین، مغازه)",
    "area": "📐 متراژ ملک چقدر است؟",
    "bedroom_count": "🛏 چند خواب دارد؟",
    "total_floors": "🏢 ساختمان چند طبقه است؟",
    "floor": "📍 واحد در چه طبقه‌ای است؟",
    "unit_count": "🚪 هر طبقه چند واحد دارد؟",
    "has_elevator": "🛗 آسانسور دارد؟ (بله / خیر)",
    "build_year": "📅 سال ساخت چه سالی است؟ (مثلاً 1402)",
    "neighborhood": "📍 ملک در کدام محله/منطقه است؟",
    "owner_name": "👤 نام شریف شما؟",
    "owner_phone": "📞 لطفاً شماره تماس خود را وارد کنید:",
    "price_total": "💰 قیمت کل ملک چقدر است؟ (به تومان)",
    "rent": "💵 مبلغ اجاره ماهیانه چقدر است؟",
    "deposit": "💳 مبلغ رهن چقدر است؟",
    "additional_features": "🏊 آیا امکانات خاصی دارد؟ (مثلا: لابی، استخر، سونا، نگهبان)\nاگر ندارد بنویسید: ندارد",
}


def _get_required_fields(data: Dict) -> list:
    """دریافت لیست فیلدهای اجباری بر اساس نوع ملک و معامله"""
    required = REQUIRED_FIELDS_BASE.copy()
    
    property_type = data.get("property_type", "").lower()
    transaction_type = data.get("transaction_type", "").lower()
    
    # فیلدهای اضافی برای آپارتمان
    if property_type in ["آپارتمان", "اپارتمان", "apartment"]:
        required.extend(APARTMENT_FIELDS)
    
    # فیلد قیمت بر اساس نوع معامله
    if "فروش" in transaction_type or "پیش" in transaction_type:
        required.append("price_total")
    elif "اجاره" in transaction_type or "رهن" in transaction_type:
        required.extend(["rent", "deposit"])
    
    return required


def _is_field_filled(data: Dict, field: str) -> bool:
    """چک کردن آیا فیلد پر شده یا نه"""
    value = data.get(field)
    
    if value is None:
        return False
    
    # برای بولی‌ها
    if isinstance(value, bool):
        return True
    
    # برای اعداد
    if isinstance(value, (int, float)):
        return value > 0
    
    # برای رشته‌ها
    if isinstance(value, str):
        return len(value.strip()) > 0
    
    return bool(value)


def run_rule_engine(data: Dict) -> Dict[str, Any]:
    """
    بررسی وضعیت داده‌ها و تعیین سوال بعدی
    """
    user_id = data.get("_user_id")
    required_fields = _get_required_fields(data)
    
    logger.debug(f"Required fields: {required_fields}")
    logger.debug(f"Current data: {data}")
    
    # پیدا کردن اولین فیلد خالی (به ترتیب FIELD_ORDER)
    for field in FIELD_ORDER:
        # فقط فیلدهای اجباری را چک کن
        if field not in required_fields:
            continue
        
        # اگر فیلد پر نشده
        if not _is_field_filled(data, field):
            question = FIELD_QUESTIONS.get(field, f"لطفاً {field} را وارد کنید:")
            
            if user_id:
                set_pending_field(user_id, field)
            
            return {
                "status": "question",
                "missing": field,
                "question": question,
                "pending_field": field,
            }
    
    # ✅ اگر همه فیلدهای اجباری پر شدند
    # چک کردن additional_features (اختیاری - فقط یک بار بپرس)
    if "additional_features" not in data or data.get("additional_features") is None:
        # اولین بار بپرس
        if user_id:
            set_pending_field(user_id, "additional_features")
        
        return {
            "status": "question",
            "missing": "additional_features",
            "question": FIELD_QUESTIONS["additional_features"],
            "pending_field": "additional_features",
        }
    
    # ✅ تمام فیلدها پر شده - به حالت completed برو
    if user_id:
        set_pending_field(user_id, None)
    
    return {
        "status": "completed",
        "data": data,
    }

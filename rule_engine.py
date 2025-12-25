# rule_engine.py - Business Rules for Property Bot
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# فیلدهای اجباری بر اساس نوع معامله
REQUIRED_FIELDS = {
    "Sale": ["transaction_type", "property_type", "area", "location", "price"],
    "Rent": ["transaction_type", "property_type", "area", "location", "rent_price"],
    "Mortgage": ["transaction_type", "property_type", "area", "location", "mortgage_amount"],
    "default": ["transaction_type", "property_type", "area", "location"]
}

# فیلدهای اختیاری
OPTIONAL_FIELDS = ["rooms", "floor", "building_age", "parking", "elevator", "storage", "description"]

# ترجمه فیلدها به فارسی
FIELD_LABELS = {
    "transaction_type": "نوع معامله",
    "property_type": "نوع ملک",
    "area": "متراژ",
    "location": "موقعیت",
    "price": "قیمت فروش",
    "rent_price": "اجاره ماهانه",
    "mortgage_amount": "مبلغ رهن",
    "rooms": "تعداد اتاق",
    "floor": "طبقه",
    "building_age": "سن بنا",
    "parking": "پارکینگ",
    "elevator": "آسانسور",
    "storage": "انباری",
    "description": "توضیحات"
}


def apply_rules(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    اعمال قوانین کسب‌وکار روی داده‌ها
    
    Returns:
        {
            "status": "complete" | "ask" | "invalid",
            "missing_fields": [...],
            "next_field": "field_name" or None,
            "message": "...",
            "data": {...}
        }
    """
    result = {
        "status": "complete",
        "missing_fields": [],
        "next_field": None,
        "message": "",
        "data": data.copy()
    }
    
    # تعیین فیلدهای اجباری بر اساس نوع معامله
    transaction_type = data.get("transaction_type", "")
    required = REQUIRED_FIELDS.get(transaction_type, REQUIRED_FIELDS["default"])
    
    # بررسی فیلدهای گمشده
    missing = []
    for field in required:
        if not data.get(field):
            missing.append(field)
    
    if missing:
        result["status"] = "ask"
        result["missing_fields"] = missing
        result["next_field"] = missing[0]
        
        # پیام برای فیلد بعدی
        field_label = FIELD_LABELS.get(missing[0], missing[0])
        result["message"] = f"لطفاً {field_label} را مشخص کنید:"
    else:
        result["status"] = "complete"
        result["message"] = "اطلاعات کامل است."
    
    return result


def validate_field(field_name: str, value: Any) -> Dict[str, Any]:
    """
    اعتبارسنجی یک فیلد خاص
    
    Returns:
        {"valid": True/False, "message": "...", "normalized_value": ...}
    """
    result = {"valid": True, "message": "", "normalized_value": value}
    
    if field_name == "area":
        try:
            area = int(str(value).replace("متر", "").replace("مربع", "").strip())
            if area < 10 or area > 10000:
                result["valid"] = False
                result["message"] = "متراژ باید بین ۱۰ تا ۱۰۰۰۰ متر باشد."
            else:
                result["normalized_value"] = area
        except ValueError:
            result["valid"] = False
            result["message"] = "لطفاً متراژ را به عدد وارد کنید."
    
    elif field_name == "price" or field_name == "rent_price" or field_name == "mortgage_amount":
        try:
            # حذف کاراکترهای اضافی
            price_str = str(value).replace(",", "").replace("تومان", "").replace("میلیون", "000000").replace("میلیارد", "000000000").strip()
            price = int(price_str)
            if price < 0:
                result["valid"] = False
                result["message"] = "قیمت نمی‌تواند منفی باشد."
            else:
                result["normalized_value"] = price
        except ValueError:
            result["valid"] = False
            result["message"] = "لطفاً قیمت را به عدد وارد کنید."
    
    elif field_name == "rooms":
        try:
            rooms = int(value)
            if rooms < 0 or rooms > 20:
                result["valid"] = False
                result["message"] = "تعداد اتاق باید بین ۰ تا ۲۰ باشد."
            else:
                result["normalized_value"] = rooms
        except ValueError:
            result["valid"] = False
            result["message"] = "لطفاً تعداد اتاق را به عدد وارد کنید."
    
    elif field_name == "floor":
        try:
            floor = int(str(value).replace("طبقه", "").strip())
            if floor < -2 or floor > 100:
                result["valid"] = False
                result["message"] = "طبقه باید بین -۲ تا ۱۰۰ باشد."
            else:
                result["normalized_value"] = floor
        except ValueError:
            result["valid"] = False
            result["message"] = "لطفاً طبقه را به عدد وارد کنید."
    
    return result


def get_missing_fields(data: Dict[str, Any]) -> List[str]:
    """دریافت لیست فیلدهای گمشده"""
    transaction_type = data.get("transaction_type", "")
    required = REQUIRED_FIELDS.get(transaction_type, REQUIRED_FIELDS["default"])
    
    missing = []
    for field in required:
        if not data.get(field):
            missing.append(field)
    
    return missing


def get_next_question(data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    دریافت سوال بعدی برای پرسیدن
    
    Returns:
        {"field": "field_name", "question": "سوال به فارسی"} or None
    """
    missing = get_missing_fields(data)
    
    if not missing:
        return None
    
    field = missing[0]
    questions = {
        "transaction_type": "نوع معامله چیست؟ (فروش/اجاره/رهن)",
        "property_type": "نوع ملک چیست؟ (آپارتمان/ویلا/زمین/مغازه)",
        "area": "متراژ ملک چند متر است؟",
        "location": "موقعیت ملک کجاست؟ (شهر و محله)",
        "price": "قیمت فروش چقدر است؟",
        "rent_price": "اجاره ماهانه چقدر است؟",
        "mortgage_amount": "مبلغ رهن چقدر است؟",
        "rooms": "چند اتاق خواب دارد؟",
        "floor": "طبقه چندم است؟"
    }
    
    return {
        "field": field,
        "question": questions.get(field, f"لطفاً {FIELD_LABELS.get(field, field)} را وارد کنید:")
    }


def format_summary(data: Dict[str, Any]) -> str:
    """فرمت‌بندی خلاصه اطلاعات ملک"""
    lines = ["📋 **خلاصه اطلاعات ملک:**", ""]
    
    field_order = [
        "transaction_type", "property_type", "area", "location",
        "price", "rent_price", "mortgage_amount",
        "rooms", "floor", "building_age",
        "parking", "elevator", "storage", "description"
    ]
    
    for field in field_order:
        value = data.get(field)
        if value:
            label = FIELD_LABELS.get(field, field)
            
            # فرمت‌بندی مقادیر خاص
            if field == "area":
                value = f"{value} متر مربع"
            elif field in ["price", "rent_price", "mortgage_amount"]:
                value = f"{value:,} تومان"
            elif field in ["parking", "elevator", "storage"]:
                value = "دارد ✅" if value else "ندارد ❌"
            
            lines.append(f"• **{label}:** {value}")
    
    return "\n".join(lines)


def is_complete(data: Dict[str, Any]) -> bool:
    """بررسی کامل بودن اطلاعات"""
    missing = get_missing_fields(data)
    return len(missing) == 0

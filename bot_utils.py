# bot_utils.py - Helper Functions
from typing import Dict, Optional

# Field Name Mapping
FIELD_NAMES_FA = {
    "نوع معامله": "transaction_type",
    "معامله": "transaction_type",
    "نوع ملک": "property_type",
    "ملک": "property_type",
    "نوع کاربری": "usage_type",
    "کاربری": "usage_type",
    "محله": "neighborhood",
    "منطقه": "neighborhood",
    "شهر": "city",
    "متراژ": "area",
    "متر": "area",
    "اتاق": "bedroom_count",
    "خواب": "bedroom_count",
    "تعداد اتاق": "bedroom_count",
    "طبقه": "floor",
    "کل طبقات": "total_floors",
    "تعداد طبقات": "total_floors",
    "واحد در طبقه": "unit_count",
    "تعداد واحد": "unit_count",
    "آسانسور": "has_elevator",
    "پارکینگ": "has_parking",
    "انباری": "has_storage",
    "سال ساخت": "build_year",
    "قیمت": "price_total",
    "رهن": "price_total",
    "اجاره": "rent",
    "نام": "owner_name",
    "نام مالک": "owner_name",
    "اسم": "owner_name",
    "تلفن": "owner_phone",
    "شماره": "owner_phone",
    "موبایل": "owner_phone",
    # ✅ اضافه شده برای امکانات
    "امکانات": "additional_features",
    "ویژگی": "additional_features",
    "ویژگی‌ها": "additional_features",
    "امکانات خاص": "additional_features",
}


# ✅ نگاشت مقادیر انگلیسی به فارسی
VALUE_TRANSLATION = {
    "Sale": "فروش",
    "Rent": "رهن و اجاره",
    "Pre-sale": "پیش‌فروش",
    "Apartment": "آپارتمان",
    "Villa": "ویلا",
    "Land": "زمین",
    "Shop": "مغازه",
    "Residential": "مسکونی",
    "Commercial": "تجاری",
    "Administrative": "اداری",
}

def translate_to_farsi(value: str) -> str:
    """ترجمه مقادیر انگلیسی به فارسی"""
    if not isinstance(value, str):
        return value
    return VALUE_TRANSLATION.get(value, value)

def is_number_only(text: str) -> bool:
    """Check if text contains only numbers"""
    try:
        clean = text.strip().replace(",", "").replace(" ", "").replace("'", "")
        float(clean)
        return True
    except ValueError:
        return False

def text_to_int(text: str) -> Optional[int]:
    """Convert text (Persian/English/Words) to integer"""
    clean = text.strip().lower()

    # Persian to English digits
    persian_digits = {
        "۱":"1", "۲":"2", "۳":"3", "۴":"4", "۵":"5",
        "۶":"6", "۷":"7", "۸":"8", "۹":"9", "۰":"0"
    }
    for p, e in persian_digits.items():
        clean = clean.replace(p, e)

    # Word to number mapping
    word_map = {
        "یک": 1, "دو": 2, "سه": 3, "چهار": 4, "پنج": 5,
        "شش": 6, "هفت": 7, "هشت": 8, "نه": 9, "ده": 10,
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6
    }

    if clean in word_map:
        return word_map[clean]

    try:
        val = float(clean.replace(",", ""))
        return int(val)
    except:
        return None

def normalize_yes_no(value: Optional[str]) -> Optional[bool]:
    """Normalize yes/no responses to boolean"""
    if value is None:
        return None

    val = str(value).strip().lower()

    if val in {"بله", "اره", "آره", "دارد", "هست", "yes", "true", "1", "ok"}:
        return True

    if val in {"نه", "خیر", "ندارد", "نیست", "no", "false", "0"}:
        return False

    return None

def format_property_summary(data: Dict) -> str:
    """Format property data as summary text"""
    lines = ["خلاصه اطلاعات ملک:"]
    lines.append("=" * 30)

    if data.get("transaction_type"):
        # ✅ ترجمه به فارسی
        lines.append(f"نوع معامله: {translate_to_farsi(data['transaction_type'])}")
    
    if data.get("property_type"):
        # ✅ ترجمه به فارسی
        lines.append(f"نوع ملک: {translate_to_farsi(data['property_type'])}")
    
    if data.get("usage_type"):
        # ✅ ترجمه به فارسی
        lines.append(f"نوع کاربری: {translate_to_farsi(data['usage_type'])}")
    
    if data.get("neighborhood"):
        lines.append(f"محله: {data['neighborhood']}")
    
    if data.get("city"):
        lines.append(f"شهر: {data['city']}")
    
    if data.get("area"):
        lines.append(f"متراژ: {data['area']} متر")
    
    if data.get("bedroom_count"):
        lines.append(f"تعداد اتاق: {data['bedroom_count']}")
    
    if data.get("total_floors"):
        lines.append(f"تعداد کل طبقات: {data['total_floors']}")
    
    if data.get("floor"):
        lines.append(f"واحد در چه طبقه‌ای است: {data['floor']}")
    
    if data.get("unit_count"):
        lines.append(f"واحد در طبقه: {data['unit_count']}")
    
    if data.get("has_elevator") is not None:
        lines.append(f"آسانسور: {'دارد' if data['has_elevator'] else 'ندارد'}")
    
    if data.get("build_year"):
        lines.append(f"سال ساخت: {data['build_year']}")
    
    if data.get("has_parking") is not None:
        lines.append(f"پارکینگ: {'دارد' if data['has_parking'] else 'ندارد'}")
    
    if data.get("has_storage") is not None:
        lines.append(f"انباری: {'دارد' if data['has_storage'] else 'ندارد'}")
    
    if data.get("price_total"):
        lines.append(f"قیمت/رهن: {data['price_total']:,.0f} تومان")
    
    if data.get("rent"):
        lines.append(f"اجاره: {data['rent']:,.0f} تومان")
    
    if data.get("owner_name"):
        lines.append(f"نام مالک: {data['owner_name']}")
    
    if data.get("owner_phone"):
        lines.append(f"تلفن: {data['owner_phone']}")
        
    if data.get("additional_features"):
        lines.append(f"امکانات: {data['additional_features']}")

    lines.append("=" * 30)
    return "\n".join(lines)

def format_confirmation_message(data: Dict) -> str:
    """Format confirmation message with edit guide"""
    summary = format_property_summary(data)
    edit_guide = (
        "\n\nبرای ویرایش هر فیلد، از فرمت زیر استفاده کنید:\n"
        "محله: گلسار\n"
        "متراژ: 120\n"
        "قیمت: 5000000000\n\n"
        "اگر اطلاعات صحیح است، 'تایید' یا 'بله' بفرستید."
    )
    return summary + edit_guide

def parse_field_from_text(text: str) -> Optional[tuple]:
    """Parse field edit request (e.g., 'محله: گلسار')"""
    text = text.strip()

    if ":" not in text and "=" not in text:
        return None

    separator = ":" if ":" in text else "="
    parts = text.split(separator, 1)

    if len(parts) != 2:
        return None

    field_name_fa = parts[0].strip()
    field_value = parts[1].strip()

    field_name_en = FIELD_NAMES_FA.get(field_name_fa)

    if not field_name_en:
        return None

    return (field_name_en, field_value)

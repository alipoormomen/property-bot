# bot_processor_core/utils.py
"""توابع کمکی پردازشگر"""

from typing import Optional
from telegram import ReplyKeyboardMarkup
from .constants import KEYBOARD_OPTIONS, BUTTON_VALUE_MAP


def normalize_button_input(text: str):
    """تبدیل متن دکمه به مقدار واقعی"""
    text = text.strip()
    return BUTTON_VALUE_MAP.get(text, text)


def is_button_input(original_text: str, normalized_text) -> bool:
    """بررسی آیا ورودی از دکمه بوده"""
    return original_text.strip() in BUTTON_VALUE_MAP


def get_reply_keyboard(field: str) -> Optional[ReplyKeyboardMarkup]:
    """دریافت کیبورد مناسب برای فیلد"""
    if field in KEYBOARD_OPTIONS:
        return ReplyKeyboardMarkup(
            KEYBOARD_OPTIONS[field],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    return None


def normalize_transaction_type(text: str) -> Optional[str]:
    """نرمال‌سازی نوع معامله"""
    text = text.lower().strip()
    
    if any(k in text for k in ["فروش", "خرید", "sale"]):
        return "فروش"
    if any(k in text for k in ["رهن", "اجاره", "rent"]):
        return "رهن و اجاره"
    if any(k in text for k in ["پیش", "presale", "پیش‌فروش", "پیشفروش"]):
        return "پیش‌فروش"
    
    return None


def normalize_property_type(text: str) -> Optional[str]:
    """نرمال‌سازی نوع ملک"""
    text = text.lower().strip()
    
    if any(k in text for k in ["آپارتمان", "واحد", "apartment", "اپارتمان"]):
        return "آپارتمان"
    if any(k in text for k in ["ویلا", "villa", "خانه", "ویلایی"]):
        return "ویلا"
    if any(k in text for k in ["زمین", "land"]):
        return "زمین"
    if any(k in text for k in ["مغازه", "تجاری", "shop", "فروشگاه"]):
        return "مغازه"
    if any(k in text for k in ["دفتر", "اداری", "office"]):
        return "دفتر کار"
    if any(k in text for k in ["سوله", "کارگاه", "انبار", "warehouse"]):
        return "سوله/انبار"
    
    return None


def normalize_usage_type(text: str) -> Optional[str]:
    """نرمال‌سازی نوع کاربری"""
    text = text.lower().strip()
    
    if any(k in text for k in ["مسکونی", "residential", "خانه", "آپارتمان"]):
        return "مسکونی"
    if any(k in text for k in ["تجاری", "commercial", "مغازه", "فروشگاه"]):
        return "تجاری"
    if any(k in text for k in ["اداری", "office", "دفتر"]):
        return "اداری"
    if any(k in text for k in ["صنعتی", "industrial", "کارخانه", "سوله"]):
        return "صنعتی"
    if any(k in text for k in ["کشاورزی", "agricultural", "زراعی", "باغ"]):
        return "کشاورزی"
    
    return None


def normalize_boolean_field(text: str) -> Optional[bool]:
    """نرمال‌سازی فیلدهای بله/خیر"""
    text = text.lower().strip()
    
    positive = ["بله", "دارد", "داره", "آره", "اره", "هست", "yes", "true", "1", "دارم"]
    negative = ["خیر", "ندارد", "نداره", "نه", "نیست", "no", "false", "0", "ندارم"]
    
    if any(k in text for k in positive):
        return True
    if any(k in text for k in negative):
        return False
    
    return None


def format_price_display(price: float) -> str:
    """فرمت نمایش قیمت به صورت خوانا"""
    if price is None:
        return "نامشخص"
    
    try:
        price = float(price)
        
        if price >= 1_000_000_000_000:  # تریلیون
            return f"{price / 1_000_000_000_000:.1f} هزار میلیارد تومان"
        elif price >= 1_000_000_000:  # میلیارد
            return f"{price / 1_000_000_000:.1f} میلیارد تومان"
        elif price >= 1_000_000:  # میلیون
            return f"{price / 1_000_000:.0f} میلیون تومان"
        elif price >= 1000:
            return f"{price / 1000:.0f} هزار تومان"
        else:
            return f"{price:.0f} تومان"
    except:
        return str(price)


def format_area_display(area: float) -> str:
    """فرمت نمایش متراژ"""
    if area is None:
        return "نامشخص"
    
    try:
        area = float(area)
        if area == int(area):
            return f"{int(area)} متر"
        return f"{area:.1f} متر"
    except:
        return str(area)

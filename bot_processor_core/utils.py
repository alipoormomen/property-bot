# bot_processor_core/utils.py
"""توابع کمکی پردازشگر"""

from telegram import ReplyKeyboardMarkup
from .constants import KEYBOARD_OPTIONS, BUTTON_VALUE_MAP


def normalize_button_input(text: str):
    """تبدیل متن دکمه به مقدار واقعی"""
    text = text.strip()
    return BUTTON_VALUE_MAP.get(text, text)


def is_button_input(original_text: str, normalized_text) -> bool:
    """بررسی آیا ورودی از دکمه بوده"""
    return original_text.strip() in BUTTON_VALUE_MAP


def get_reply_keyboard(field: str):
    """دریافت کیبورد مناسب برای فیلد"""
    if field in KEYBOARD_OPTIONS:
        return ReplyKeyboardMarkup(
            KEYBOARD_OPTIONS[field],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    return None


def normalize_transaction_type(text: str) -> str:
    """نرمال‌سازی نوع معامله"""
    text = text.lower().strip()
    
    if any(k in text for k in ["فروش", "خرید", "sale"]):
        return "فروش"
    if any(k in text for k in ["رهن", "اجاره", "rent"]):
        return "رهن و اجاره"
    if any(k in text for k in ["پیش", "presale"]):
        return "پیش‌فروش"
    
    return text


def normalize_property_type(text: str) -> str:
    """نرمال‌سازی نوع ملک"""
    text = text.lower().strip()
    
    if any(k in text for k in ["آپارتمان", "واحد", "apartment"]):
        return "آپارتمان"
    if any(k in text for k in ["ویلا", "villa", "خانه"]):
        return "ویلا"
    if any(k in text for k in ["زمین", "land"]):
        return "زمین"
    if any(k in text for k in ["مغازه", "تجاری", "shop"]):
        return "مغازه"
    
    return text


def normalize_usage_type(text: str) -> str:
    """نرمال‌سازی نوع کاربری"""
    text = text.lower().strip()
    
    if any(k in text for k in ["مسکونی", "residential"]):
        return "مسکونی"
    if any(k in text for k in ["
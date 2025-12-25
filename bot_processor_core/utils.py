# bot_processor_core/utils.py
"""توابع کمکی برای پردازش ورودی"""

import logging
from typing import Optional, Any
from telegram import ReplyKeyboardMarkup

from .constants import KEYBOARD_OPTIONS, BUTTON_VALUE_MAP

logger = logging.getLogger(__name__)


def get_reply_keyboard(field_name: str) -> Optional[ReplyKeyboardMarkup]:
    """ساخت ReplyKeyboard برای فیلدهای انتخابی"""
    if field_name in KEYBOARD_OPTIONS:
        return ReplyKeyboardMarkup(
            KEYBOARD_OPTIONS[field_name],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    return None


def normalize_button_input(text: str) -> Any:
    """تبدیل متن دکمه (با ایموجی) به مقدار واقعی"""
    return BUTTON_VALUE_MAP.get(text.strip(), text.strip())


def is_button_input(original_text: str, normalized: Any) -> bool:
    """بررسی اینکه آیا ورودی از دکمه بوده"""
    return normalized != original_text.strip()


def normalize_transaction_type(text: str) -> Optional[str]:
    """نرمال‌سازی نوع معامله"""
    normalized = text.lower().strip()
    if normalized in ["اجاره", "رهن", "اجارە"]:
        return "رهن و اجاره"
    elif normalized in ["فروش", "خرید"]:
        return "فروش"
    elif normalized in ["پیش فروش", "پیشفروش", "پیش‌فروش"]:
        return "پیش‌فروش"
    return None


def normalize_property_type(text: str) -> Optional[str]:
    """نرمال‌سازی نوع ملک"""
    normalized = text.lower().strip()
    mapping = {
        "آپارتمان": ["آپارتمان", "اپارتمان"],
        "ویلا": ["ویلا", "ویلایی"],
        "زمین": ["زمین"],
        "مغازه": ["مغازه", "غازه"],
    }
    for value, variants in mapping.items():
        if normalized in variants:
            return value
    return None


def normalize_usage_type(text: str) -> Optional[str]:
    """نرمال‌سازی نوع کاربری"""
    normalized = text.lower().strip()
    if normalized in ["مسکونی"]:
        return "مسکونی"
    elif normalized in ["تجاری"]:
        return "تجاری"
    elif normalized in ["اداری"]:
        return "اداری"
    return None

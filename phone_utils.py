import re
from typing import Optional

def normalize_iran_phone(phone: str) -> Optional[str]:
    """
    نرمال‌سازی شماره تلفن ایران
    ورودی: هر فرمت (با/بدون +98, 0, فاصله, خط تیره)
    خروجی: 09xxxxxxxxx یا None
    """
    if not phone:
        return None
    
    # پاکسازی کاراکترهای غیرضروری
    cleaned = re.sub(r'[^\d+]', '', str(phone))
    
    # حذف +98 یا 0098 از اول
    if cleaned.startswith('+98'):
        cleaned = '0' + cleaned[3:]
    elif cleaned.startswith('0098'):
        cleaned = '0' + cleaned[4:]
    elif cleaned.startswith('98') and len(cleaned) == 12:
        cleaned = '0' + cleaned[2:]
    
    # اضافه کردن 0 اگر نباشد
    if not cleaned.startswith('0') and len(cleaned) == 10:
        cleaned = '0' + cleaned
    
    # Validation: باید 11 رقم باشد و با 09 شروع شود
    if len(cleaned) == 11 and cleaned.startswith('09'):
        return cleaned
    
    return None

def validate_phone(phone: str) -> bool:
    """بررسی معتبر بودن شماره"""
    normalized = normalize_iran_phone(phone)
    return normalized is not None

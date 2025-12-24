# utils.py (FINAL VERSION)

import re
from typing import Union, Optional, Dict

def normalize_price(value: Union[str, int, float]) -> Optional[float]:
    """
    نرمال‌سازی قیمت به ریال
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace(',', '').replace(' ', '')

    # Persian to English digits
    persian_nums = '۰۱۲۳۴۵۶۷۸۹'
    english_nums = '0123456789'
    for p, e in zip(persian_nums, english_nums):
        text = text.replace(p, e)

    # Find number
    match = re.search(r'\d+(?:\.\d+)?', text)
    if not match:
        return None

    base_value = float(match.group())
    text_lower = text.lower()

    if 'میلیارد' in text or 'milliard' in text_lower:
        if 'تومان' in text or 'toman' in text_lower:
            return base_value * 10_000_000_000
        return base_value * 1_000_000_000

    if 'میلیون' in text or 'million' in text_lower:
        if 'تومان' in text or 'toman' in text_lower:
            return base_value * 10_000_000
        return base_value * 1_000_000

    if 'تومان' in text or 'toman' in text_lower:
        return base_value * 10

    return base_value

def validate_area(area: Union[int, float]) -> Optional[float]:
    """
    اعتبارسنجی متراژ
    بازه منطقی: 10 تا 10000 متر
    """
    if area is None: 
        return None
    try:
        val = float(area)
        if 10 <= val <= 10000:
            return val
        return None
    except:
        return None

def validate_year(year: Union[int, float, str]) -> Optional[int]:
    """
    اعتبارسنجی سال ساخت
    قبول می‌کند: شمسی (1300-1450) یا میلادی (1950-2030)
    """
    if year is None: 
        return None
    try:
        val = int(str(year).strip())
        if 1300 <= val <= 1450: 
            return val
        if 1950 <= val <= 2030: 
            return val
        return None
    except:
        return None

def validate_floor(floor: Union[int, float, str]) -> Optional[int]:
    """
    اعتبارسنجی طبقه
    بازه منطقی: -5 (زیرزمین) تا 150 (برج‌های بلند)
    """
    if floor is None: 
        return None
    try:
        val = int(str(floor).strip())
        if -5 <= val <= 150:
            return val
        return None
    except:
        return None

def validate_count(count: Union[int, float, str], field_name: str) -> Optional[int]:
    """
    اعتبارسنجی تعداد (برای خواب، پارکینگ، انباری و...)
    """
    if count is None:
        return None
    try:
        val = int(str(count).strip())
        
        # بازه‌های منطقی بر اساس نوع فیلد
        ranges = {
            "bedroom_count": (0, 10),      # 0 تا 10 خواب
            "parking_count": (0, 5),       # 0 تا 5 پارکینگ
            "storage_count": (0, 3),       # 0 تا 3 انباری
            "unit_count": (1, 20),         # 1 تا 20 واحد در طبقه
            "total_floors": (1, 150),      # 1 تا 150 طبقه
        }
        
        min_val, max_val = ranges.get(field_name, (0, 100))
        
        if min_val <= val <= max_val:
            return val
        return None
    except:
        return None

def validate_price(price: Union[int, float], transaction_type: str) -> Dict:
    """
    ✅ اعتبارسنجی قیمت با توجه به نوع معامله
    
    Returns:
        {
            "valid": bool,
            "value": Optional[int],
            "suggested": Optional[int],
            "message": Optional[str]
        }
    """
    if price is None:
        return {"valid": False, "message": "قیمت وارد نشده"}
    
    try:
        price = int(float(price))
    except:
        return {"valid": False, "message": "فرمت قیمت نامعتبر"}
    
    # بررسی برای فروش
    if transaction_type in ["فروش", "Sale", "sale"]:
        # بازه منطقی: 100 میلیون تا 50 میلیارد تومان
        if 100_000_000 <= price <= 50_000_000_000:
            return {"valid": True, "value": price}
        
        # قیمت خیلی کوچک
        if price < 100_000_000:
            suggested = price * 10  # شاید تومان به جای ریال گفته
            return {
                "valid": False,
                "suggested": suggested,
                "message": f"⚠️ قیمت {price:,} تومان بسیار کم است. منظورتان {suggested:,} تومان است؟ (بله/خیر)"
            }
        
        # قیمت خیلی بزرگ (احتمال یک صفر اضافی)
        if price > 50_000_000_000:
            suggested = price // 10
            return {
                "valid": False,
                "suggested": suggested,
                "message": f"⚠️ قیمت {price:,} تومان بسیار زیاد است. منظورتان {suggested:,} تومان است؟ (بله/خیر)"
            }
    
    # بررسی برای رهن/اجاره
    elif transaction_type in ["رهن و اجاره", "Rent", "rent", "اجاره"]:
        # رهن: 10 میلیون تا 10 میلیارد
        if 10_000_000 <= price <= 10_000_000_000:
            return {"valid": True, "value": price}
        
        if price < 10_000_000:
            suggested = price * 10
            return {
                "valid": False,
                "suggested": suggested,
                "message": f"⚠️ مبلغ رهن {price:,} تومان بسیار کم است. منظورتان {suggested:,} تومان است؟"
            }
        
        if price > 10_000_000_000:
            suggested = price // 10
            return {
                "valid": False,
                "suggested": suggested,
                "message": f"⚠️ مبلغ رهن {price:,} تومان بسیار زیاد است. منظورتان {suggested:,} تومان است؟"
            }
    
    # اگر نوع معامله مشخص نیست
    return {"valid": True, "value": price}

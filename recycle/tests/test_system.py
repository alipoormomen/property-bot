"""
اسکریپت تست کامل سیستم
"""
import sys
from phone_utils import normalize_iran_phone, validate_phone
from utils import normalize_price, validate_area, validate_floor

def test_phone_normalization():
    """تست نرمال‌سازی شماره تلفن"""
    print("=" * 50)
    print("📱 تست شماره تلفن")
    print("=" * 50)
    
    test_cases = [
        ("911-233-455", "09112334550"),  # فرمت STT
        ("09112334550", "09112334550"),  # فرمت صحیح
        ("+989112334550", "09112334550"),  # با کد کشور
        ("00989112334550", "09112334550"),  # با 0098
        ("9112334550", "09112334550"),  # بدون 0
        ("021 1234 5678", None),  # شماره ثابت (نامعتبر)
        ("123", None),  # خیلی کوتاه
    ]
    
    passed = 0
    for input_phone, expected in test_cases:
        result = normalize_iran_phone(input_phone)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_phone}' → {result} (انتظار: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\nنتیجه: {passed}/{len(test_cases)} موفق")
    return passed == len(test_cases)

def test_price_normalization():
    """تست نرمال‌سازی قیمت"""
    print("\n" + "=" * 50)
    print("💰 تست نرمال‌سازی قیمت")
    print("=" * 50)
    
    test_cases = [
        ("ده میلیارد تومن", 100_000_000_000),
        ("10 میلیارد تومان", 100_000_000_000),
        ("بیست میلیون", 200_000_000),  # فرض: ریال
        ("۲۰ میلیون تومان", 200_000_000),
        (10000000, 10000000),  # عدد خام
        ("5.5 میلیارد تومان", 55_000_000_000),
    ]
    
    passed = 0
    for input_price, expected in test_cases:
        result = normalize_price(input_price)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_price}' → {result:,.0f} (انتظار: {expected:,.0f})")
        if result == expected:
            passed += 1
    
    print(f"\nنتیجه: {passed}/{len(test_cases)} موفق")
    return passed == len(test_cases)

def test_area_validation():
    """تست اعتبارسنجی متراژ"""
    print("\n" + "=" * 50)
    print("📐 تست اعتبارسنجی متراژ")
    print("=" * 50)
    
    test_cases = [
        (50, True),
        (400, True),
        (5, False),  # خیلی کوچک
        (15000, False),  # خیلی بزرگ
        (-10, False),  # منفی
    ]
    
    passed = 0
    for area, expected in test_cases:
        result = validate_area(area)
        status = "✅" if result == expected else "❌"
        print(f"{status} متراژ {area} → {result} (انتظار: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\nنتیجه: {passed}/{len(test_cases)} موفق")
    return passed == len(test_cases)

def test_floor_validation():
    """تست اعتبارسنجی طبقه"""
    print("\n" + "=" * 50)
    print("🏢 تست اعتبارسنجی طبقه")
    print("=" * 50)
    
    test_cases = [
        (0, True),  # همکف
        (10, True),
        (-2, True),  # زیرزمین
        (150, False),  # خیلی بالا
        (-10, False),  # زیرزمین عمیق
    ]
    
    passed = 0
    for floor, expected in test_cases:
        result = validate_floor(floor)
        status = "✅" if result == expected else "❌"
        print(f"{status} طبقه {floor} → {result} (انتظار: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\nنتیجه: {passed}/{len(test_cases)} موفق")
    return passed == len(test_cases)

def main():
    """اجرای تمام تست‌ها"""
    print("\n🚀 شروع تست کامل سیستم\n")
    
    results = {
        "Phone": test_phone_normalization(),
        "Price": test_price_normalization(),
        "Area": test_area_validation(),
        "Floor": test_floor_validation(),
    }
    
    print("\n" + "=" * 50)
    print("📊 خلاصه نتایج")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 همه تست‌ها موفق!" if all_passed else "⚠️ برخی تست‌ها ناموفق"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

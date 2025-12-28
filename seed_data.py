# seed_data.py
"""درج داده‌های اولیه در NocoDB"""

import asyncio
from nocodb_client import _request, _table_url

async def seed_packages():
    """درج بسته‌های اعتباری"""
    packages = [
        {
            "name": "پایه",
            "price": 25000,
            "credit_amount": 25000,
            "bonus_percent": 0,
            "description": "بسته شروع - بدون بونوس",
            "is_active": True
        },
        {
            "name": "استاندارد", 
            "price": 50000,
            "credit_amount": 50000,
            "bonus_percent": 5,
            "description": "۵٪ اعتبار هدیه",
            "is_active": True
        },
        {
            "name": "حرفه‌ای",
            "price": 100000,
            "credit_amount": 100000,
            "bonus_percent": 10,
            "description": "۱۰٪ اعتبار هدیه",
            "is_active": True
        },
        {
            "name": "سازمانی",
            "price": 250000,
            "credit_amount": 250000,
            "bonus_percent": 20,
            "description": "۲۰٪ اعتبار هدیه - بهترین ارزش",
            "is_active": True
        }
    ]
    
    print("📦 درج بسته‌ها...")
    for pkg in packages:
        result = await _request("POST", _table_url("packages"), pkg)
        print(f"   ✅ {pkg['name']}: {result.get('Id')}")
    
    return len(packages)


async def seed_ai_config():
    """درج تنظیمات AI"""
    configs = [
        {
            "model_name": "gpt-4o-mini",
            "provider": "avalai",
            "input_price_per_1k": 22.5,
            "output_price_per_1k": 90,
            "is_active": True
        },
        {
            "model_name": "whisper-1",
            "provider": "avalai", 
            "input_price_per_1k": 150,  # تقریبی برای هر دقیقه صوت
            "output_price_per_1k": 0,
            "is_active": True
        }
    ]
    
    print("⚙️ درج تنظیمات AI...")
    for cfg in configs:
        result = await _request("POST", _table_url("ai_config"), cfg)
        print(f"   ✅ {cfg['model_name']}: {result.get('Id')}")
    
    return len(configs)


async def main():
    print("=" * 40)
    print("🌱 شروع درج داده‌های اولیه")
    print("=" * 40)
    
    try:
        pkg_count = await seed_packages()
        ai_count = await seed_ai_config()
        
        print("=" * 40)
        print(f"✅ تمام شد!")
        print(f"   📦 {pkg_count} بسته")
        print(f"   ⚙️ {ai_count} تنظیم AI")
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ خطا: {e}")


if __name__ == "__main__":
    asyncio.run(main())

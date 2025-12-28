# recreate_packages.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")
BASE_ID = "p1lsnufyyyjcf1p"  # ✅ Base ID صحیح

headers = {"xc-token": NOCODB_TOKEN}

# 1️⃣ ساخت جدول packages جدید
print("🔧 ساخت جدول packages...")

table_schema = {
    "table_name": "packages",
    "title": "packages",
    "columns": [
        {"column_name": "Id", "title": "Id", "uidt": "ID"},  # Primary Key
        {"column_name": "name", "title": "name", "uidt": "SingleLineText"},
        {"column_name": "price", "title": "price", "uidt": "Number"},  # مبلغ پرداختی (تومان)
        {"column_name": "credit", "title": "credit", "uidt": "Number"},  # اعتبار دریافتی (تومان)
        {"column_name": "description", "title": "description", "uidt": "LongText"},
        {"column_name": "is_active", "title": "is_active", "uidt": "Checkbox"},
    ]
}

resp = httpx.post(
    f"{NOCODB_URL}/api/v2/meta/bases/{BASE_ID}/tables",
    headers=headers,
    json=table_schema
)

if resp.status_code in [200, 201]:
    table_data = resp.json()
    table_id = table_data.get("id")
    print(f"✅ جدول ساخته شد! Table ID: {table_id}")
    
    # 2️⃣ درج بسته‌های پیشنهادی
    print("\n📦 درج بسته‌ها...")
    
    packages = [
        {"name": "استارتر", "price": 50000, "credit": 25000, "description": "بسته شروع - مناسب آشنایی", "is_active": True},
        {"name": "اقتصادی", "price": 150000, "credit": 80000, "description": "بسته اقتصادی - مناسب مصرف متوسط", "is_active": True},
        {"name": "حرفه‌ای", "price": 350000, "credit": 200000, "description": "بسته حرفه‌ای - مناسب آژانس‌های کوچک", "is_active": True},
        {"name": "سازمانی", "price": 800000, "credit": 500000, "description": "بسته سازمانی - مناسب آژانس‌های بزرگ", "is_active": True},
    ]
    
    for pkg in packages:
        r = httpx.post(
            f"{NOCODB_URL}/api/v2/tables/{table_id}/records",
            headers=headers,
            json=pkg
        )
        if r.status_code in [200, 201]:
            print(f"   ✅ {pkg['name']}: {pkg['price']:,} تومان → {pkg['credit']:,} اعتبار")
        else:
            print(f"   ❌ خطا در درج {pkg['name']}: {r.text}")
    
    print("\n🎉 تمام!")
else:
    print(f"❌ خطا در ساخت جدول: {resp.status_code}")
    print(resp.text)

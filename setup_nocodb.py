#!/usr/bin/env python3
"""
اسکریپت ساخت خودکار Tables در NocoDB
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# تنظیمات
BASE_URL = os.getenv("NOCODB_BASE_URL", "http://localhost:8080")
API_TOKEN = os.getenv("NOCODB_API_TOKEN")

if not API_TOKEN:
    print("❌ NOCODB_API_TOKEN در .env تنظیم نشده!")
    exit(1)

HEADERS = {
    "xc-token": API_TOKEN,
    "Content-Type": "application/json"
}

# =============================================
# تعریف Schema کامل
# =============================================

TABLES_SCHEMA = {
    "users": {
        "columns": [
            {"column_name": "telegram_id", "uidt": "Number", "rqd": True, "un": True},
            {"column_name": "phone", "uidt": "SingleLineText"},
            {"column_name": "first_name", "uidt": "SingleLineText"},
            {"column_name": "last_name", "uidt": "SingleLineText"},
            {"column_name": "username", "uidt": "SingleLineText"},
            {"column_name": "balance", "uidt": "Number", "cdf": "0"},
            {"column_name": "total_charged", "uidt": "Number", "cdf": "0"},
            {"column_name": "total_used", "uidt": "Number", "cdf": "0"},
            {"column_name": "is_active", "uidt": "Checkbox", "cdf": "1"},
            {"column_name": "created_at", "uidt": "DateTime"},
            {"column_name": "last_activity", "uidt": "DateTime"},
        ]
    },
    "properties": {
        "columns": [
            {"column_name": "transaction_type", "uidt": "SingleSelect", 
             "dtxp": "'sale','rent','mortgage'"},
            {"column_name": "property_type", "uidt": "SingleSelect",
             "dtxp": "'apartment','villa','land','commercial','other'"},
            {"column_name": "city", "uidt": "SingleLineText"},
            {"column_name": "neighborhood", "uidt": "SingleLineText"},
            {"column_name": "address", "uidt": "LongText"},
            {"column_name": "area", "uidt": "Number"},
            {"column_name": "rooms", "uidt": "Number"},
            {"column_name": "floor", "uidt": "Number"},
            {"column_name": "total_floors", "uidt": "Number"},
            {"column_name": "year_built", "uidt": "Number"},
            {"column_name": "total_price", "uidt": "Number"},
            {"column_name": "price_per_meter", "uidt": "Number"},
            {"column_name": "rent_price", "uidt": "Number"},
            {"column_name": "deposit", "uidt": "Number"},
            {"column_name": "features", "uidt": "LongText"},
            {"column_name": "description", "uidt": "LongText"},
            {"column_name": "owner_phone", "uidt": "SingleLineText"},
            {"column_name": "owner_name", "uidt": "SingleLineText"},
            {"column_name": "raw_text", "uidt": "LongText"},
            {"column_name": "source_type", "uidt": "SingleSelect",
             "dtxp": "'voice','text','forward'"},
            {"column_name": "input_tokens", "uidt": "Number", "cdf": "0"},
            {"column_name": "output_tokens", "uidt": "Number", "cdf": "0"},
            {"column_name": "audio_seconds", "uidt": "Number", "cdf": "0"},
            {"column_name": "cost_toman", "uidt": "Number", "cdf": "0"},
            {"column_name": "created_at", "uidt": "DateTime"},
        ]
    },
    "transactions": {
        "columns": [
            {"column_name": "type", "uidt": "SingleSelect",
             "dtxp": "'charge','usage','bonus','refund'"},
            {"column_name": "amount", "uidt": "Number"},
            {"column_name": "balance_before", "uidt": "Number"},
            {"column_name": "balance_after", "uidt": "Number"},
            {"column_name": "description", "uidt": "SingleLineText"},
            {"column_name": "payment_ref", "uidt": "SingleLineText"},
            {"column_name": "created_at", "uidt": "DateTime"},
        ]
    },
    "packages": {
        "columns": [
            {"column_name": "name", "uidt": "SingleLineText"},
            {"column_name": "price", "uidt": "Number"},
            {"column_name": "credit", "uidt": "Number"},
            {"column_name": "bonus_percent", "uidt": "Number", "cdf": "0"},
            {"column_name": "is_active", "uidt": "Checkbox", "cdf": "1"},
            {"column_name": "sort_order", "uidt": "Number", "cdf": "0"},
        ]
    },
    "ai_config": {
        "columns": [
            {"column_name": "service", "uidt": "SingleLineText"},
            {"column_name": "input_rate_usd", "uidt": "Decimal"},
            {"column_name": "output_rate_usd", "uidt": "Decimal"},
            {"column_name": "audio_rate_usd", "uidt": "Decimal"},
            {"column_name": "usd_rate", "uidt": "Number"},
            {"column_name": "updated_at", "uidt": "DateTime"},
        ]
    }
}

# داده‌های اولیه
INITIAL_DATA = {
    "packages": [
        {"name": "استارتر", "price": 25000, "credit": 25000, "bonus_percent": 0, "is_active": True, "sort_order": 1},
        {"name": "استاندارد", "price": 50000, "credit": 55000, "bonus_percent": 10, "is_active": True, "sort_order": 2},
        {"name": "حرفه‌ای", "price": 100000, "credit": 115000, "bonus_percent": 15, "is_active": True, "sort_order": 3},
        {"name": "ویژه", "price": 250000, "credit": 300000, "bonus_percent": 20, "is_active": True, "sort_order": 4},
    ],
    "ai_config": [
        {"service": "gpt-4o-mini", "input_rate_usd": 0.00000015, "output_rate_usd": 0.0000006, "audio_rate_usd": 0, "usd_rate": 150000},
        {"service": "whisper", "input_rate_usd": 0, "output_rate_usd": 0, "audio_rate_usd": 0.0001, "usd_rate": 150000},
    ]
}


def get_bases():
    """لیست همه Bases"""
    resp = requests.get(f"{BASE_URL}/api/v2/meta/bases", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("list", [])


def get_base_id(base_name="PropertyBot"):
    """پیدا کردن Base ID"""
    bases = get_bases()
    for base in bases:
        if base.get("title") == base_name:
            return base.get("id")
    return None


def get_tables(base_id):
    """لیست Tables یک Base"""
    resp = requests.get(f"{BASE_URL}/api/v2/meta/bases/{base_id}/tables", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("list", [])


def create_table(base_id, table_name, columns):
    """ساخت Table با ستون‌ها"""
    payload = {
        "table_name": table_name,
        "title": table_name,
        "columns": columns
    }
    resp = requests.post(
        f"{BASE_URL}/api/v2/meta/bases/{base_id}/tables",
        headers=HEADERS,
        json=payload
    )
    resp.raise_for_status()
    return resp.json()


def add_link_column(table_id, column_name, parent_table_id):
    """اضافه کردن ستون Link"""
    payload = {
        "column_name": column_name,
        "uidt": "Links",
        "parentId": parent_table_id,
        "type": "bt"  # belongs to
    }
    resp = requests.post(
        f"{BASE_URL}/api/v2/meta/tables/{table_id}/columns",
        headers=HEADERS,
        json=payload
    )
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"   ⚠️ Link column error: {resp.text}")
        return None


def insert_rows(table_id, rows):
    """درج ردیف‌ها"""
    resp = requests.post(
        f"{BASE_URL}/api/v2/tables/{table_id}/records",
        headers=HEADERS,
        json=rows
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print("=" * 50)
    print("🚀 شروع ساخت خودکار Tables در NocoDB")
    print("=" * 50)
    
    # پیدا کردن Base
    base_id = get_base_id("PropertyBot")
    if not base_id:
        print("❌ Base با نام 'PropertyBot' پیدا نشد!")
        print("   لطفاً اول یه Base خالی با این نام بساز.")
        return
    
    print(f"✅ Base پیدا شد: {base_id}")
    
    # چک کردن Tables موجود
    existing_tables = get_tables(base_id)
    existing_names = [t.get("title") for t in existing_tables]
    print(f"📋 Tables موجود: {existing_names}")
    
    created_tables = {}
    
    # ساخت Tables
    for table_name, schema in TABLES_SCHEMA.items():
        if table_name in existing_names:
            print(f"⏭️  {table_name} - قبلاً وجود داره")
            # پیدا کردن ID
            for t in existing_tables:
                if t.get("title") == table_name:
                    created_tables[table_name] = t.get("id")
            continue
        
        print(f"📦 ساخت {table_name}...")
        try:
            result = create_table(base_id, table_name, schema["columns"])
            table_id = result.get("id")
            created_tables[table_name] = table_id
            print(f"   ✅ ساخته شد: {table_id}")
        except Exception as e:
            print(f"   ❌ خطا: {e}")
    
    # اضافه کردن Links
    print("\n🔗 اضافه کردن روابط...")
    
    if "properties" in created_tables and "users" in created_tables:
        print("   → properties.user_id → users")
        add_link_column(created_tables["properties"], "user_id", created_tables["users"])
    
    if "transactions" in created_tables and "users" in created_tables:
        print("   → transactions.user_id → users")
        add_link_column(created_tables["transactions"], "user_id", created_tables["users"])
    
    if "transactions" in created_tables and "properties" in created_tables:
        print("   → transactions.property_id → properties")
        add_link_column(created_tables["transactions"], "property_id", created_tables["properties"])
    
    # درج داده‌های اولیه
    print("\n📝 درج داده‌های اولیه...")
    
    for table_name, rows in INITIAL_DATA.items():
        if table_name in created_tables:
            print(f"   → {table_name}: {len(rows)} ردیف")
            try:
                insert_rows(created_tables[table_name], rows)
                print(f"      ✅ درج شد")
            except Exception as e:
                print(f"      ⚠️ خطا: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 تمام! Tables ساخته شدند.")
    print("=" * 50)
    
    print("\n📋 خلاصه Table IDs:")
    for name, tid in created_tables.items():
        print(f"   {name}: {tid}")


if __name__ == "__main__":
    main()

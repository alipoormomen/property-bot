# nocodb_client.py - آپدیت شده با Table IDهای واقعی
"""
NocoDB Client - ماژول ارتباط با دیتابیس
"""

import os
import httpx
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════
# تنظیمات اتصال
# ═══════════════════════════════════════════════════════════

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

# Table IDs - از NocoDB استخراج شده
TABLES = {
    "users": "m2exwsn2lm2scg7",
    "properties": "mwgik4tnx5fdrls", 
    "transactions": "mn0clzygu0ex3lq",
    "packages": "mv3d40e9u4xlmi2",  # ✅ جدید
    "ai_config": "mea2jyex8qolo6t",
}


def _headers():
    return {"xc-token": NOCODB_TOKEN}

def _table_url(table_name: str) -> str:
    """ساخت URL برای دسترسی به جدول"""
    table_id = TABLES.get(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found in TABLES config")
    return f"{NOCODB_URL}/api/v2/tables/{table_id}/records"


# ═══════════════════════════════════════════════════════════
# مدیریت کاربران
# ═══════════════════════════════════════════════════════════

async def get_user(telegram_id: int) -> Optional[dict]:
    """دریافت اطلاعات کاربر با telegram_id"""
    async with httpx.AsyncClient() as client:
        url = _table_url("users")
        params = {"where": f"(telegram_id,eq,{telegram_id})"}
        resp = await client.get(url, headers=_headers(), params=params)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get("list", [])
            return records[0] if records else None
    return None


async def create_user(telegram_id: int, username: str = None, 
                      first_name: str = None, phone: str = None) -> dict:
    """ایجاد کاربر جدید"""
    async with httpx.AsyncClient() as client:
        url = _table_url("users")
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "phone": phone,
            "credit_balance": 0,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
        }
        resp = await client.post(url, headers=_headers(), json=payload)
        return resp.json()


async def get_or_create_user(telegram_id: int, **kwargs) -> dict:
    """دریافت یا ایجاد کاربر"""
    user = await get_user(telegram_id)
    if user:
        return user
    return await create_user(telegram_id, **kwargs)


async def update_user_credit(telegram_id: int, new_balance: int) -> bool:
    """بروزرسانی اعتبار کاربر"""
    user = await get_user(telegram_id)
    if not user:
        return False
    
    async with httpx.AsyncClient() as client:
        url = _table_url("users")
        payload = {
            "Id": user["Id"],
            "credit_balance": new_balance
        }
        resp = await client.patch(url, headers=_headers(), json=payload)
        return resp.status_code == 200


async def add_credit(telegram_id: int, amount: int) -> Optional[int]:
    """افزایش اعتبار کاربر - برمی‌گرداند موجودی جدید"""
    user = await get_user(telegram_id)
    if not user:
        return None
    
    new_balance = user.get("credit_balance", 0) + amount
    success = await update_user_credit(telegram_id, new_balance)
    return new_balance if success else None


async def deduct_credit(telegram_id: int, amount: int) -> Optional[int]:
    """کسر اعتبار کاربر - برمی‌گرداند موجودی جدید یا None اگر موجودی کافی نباشد"""
    user = await get_user(telegram_id)
    if not user:
        return None
    
    current = user.get("credit_balance", 0)
    if current < amount:
        return None  # موجودی کافی نیست
    
    new_balance = current - amount
    success = await update_user_credit(telegram_id, new_balance)
    return new_balance if success else None


async def get_user_credit(telegram_id: int) -> int:
    """دریافت موجودی فعلی کاربر"""
    user = await get_user(telegram_id)
    if user:
        return user.get("credit_balance", 0)
    return 0


# ═══════════════════════════════════════════════════════════
# مدیریت ملک‌ها
# ═══════════════════════════════════════════════════════════

async def create_property(user_telegram_id: int, property_data: dict) -> dict:
    """ذخیره ملک جدید"""
    async with httpx.AsyncClient() as client:
        url = _table_url("properties")
        
        payload = {
            "user_telegram_id": user_telegram_id,
            "property_type": property_data.get("property_type"),
            "transaction_type": property_data.get("transaction_type"),
            "city": property_data.get("city"),
            "district": property_data.get("district"),
            "area_meters": property_data.get("area"),
            "rooms": property_data.get("rooms"),
            "price": property_data.get("price"),
            "price_per_meter": property_data.get("price_per_meter"),
            "deposit": property_data.get("deposit"),
            "rent": property_data.get("rent"),
            "floor": property_data.get("floor"),
            "total_floors": property_data.get("total_floors"),
            "features": ",".join(property_data.get("features", [])),
            "raw_text": property_data.get("raw_text"),
            "created_at": datetime.now().isoformat(),
        }
        
        # حذف مقادیر None
        payload = {k: v for k, v in payload.items() if v is not None}
        
        resp = await client.post(url, headers=_headers(), json=payload)
        return resp.json()


async def get_user_properties(telegram_id: int, limit: int = 10) -> list:
    """دریافت ملک‌های کاربر"""
    async with httpx.AsyncClient() as client:
        url = _table_url("properties")
        params = {
            "where": f"(user_telegram_id,eq,{telegram_id})",
            "limit": limit,
            "sort": "-created_at"
        }
        resp = await client.get(url, headers=_headers(), params=params)
        if resp.status_code == 200:
            return resp.json().get("list", [])
    return []


# ═══════════════════════════════════════════════════════════
# مدیریت تراکنش‌ها
# ═══════════════════════════════════════════════════════════

async def create_transaction(
    user_telegram_id: int,
    trans_type: str,  # "charge" | "usage" | "refund"
    amount: int,
    description: str = None,
    package_id: int = None,
    ai_model: str = None,
    tokens_used: int = None
) -> dict:
    """ثبت تراکنش جدید"""
    async with httpx.AsyncClient() as client:
        url = _table_url("transactions")
        
        payload = {
            "user_telegram_id": user_telegram_id,
            "type": trans_type,
            "amount": amount,
            "description": description,
            "package_id": package_id,
            "ai_model": ai_model,
            "tokens_used": tokens_used,
            "created_at": datetime.now().isoformat(),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        resp = await client.post(url, headers=_headers(), json=payload)
        return resp.json()


async def get_user_transactions(telegram_id: int, limit: int = 20) -> list:
    """دریافت تاریخچه تراکنش‌های کاربر"""
    async with httpx.AsyncClient() as client:
        url = _table_url("transactions")
        params = {
            "where": f"(user_telegram_id,eq,{telegram_id})",
            "limit": limit,
            "sort": "-created_at"
        }
        resp = await client.get(url, headers=_headers(), params=params)
        if resp.status_code == 200:
            return resp.json().get("list", [])
    return []


# ═══════════════════════════════════════════════════════════
# مدیریت بسته‌ها و تنظیمات
# ═══════════════════════════════════════════════════════════

async def get_active_packages() -> list:
    """دریافت لیست بسته‌های فعال"""
    async with httpx.AsyncClient() as client:
        url = _table_url("packages")
        params = {
            "where": "(is_active,eq,true)",
            "sort": "sort_order"
        }
        resp = await client.get(url, headers=_headers(), params=params)
        if resp.status_code == 200:
            return resp.json().get("list", [])
    return []


async def get_package_by_id(package_id: int) -> Optional[dict]:
    """دریافت اطلاعات یک بسته"""
    async with httpx.AsyncClient() as client:
        url = f"{_table_url('packages')}/{package_id}"
        resp = await client.get(url, headers=_headers())
        if resp.status_code == 200:
            return resp.json()
    return None


async def get_ai_config(model_name: str = "gpt-4o-mini") -> Optional[dict]:
    """دریافت تنظیمات مدل AI"""
    async with httpx.AsyncClient() as client:
        url = _table_url("ai_config")
        params = {"where": f"(model_name,eq,{model_name})"}
        resp = await client.get(url, headers=_headers(), params=params)
        if resp.status_code == 200:
            records = resp.json().get("list", [])
            return records[0] if records else None
    return None


# ═══════════════════════════════════════════════════════════
# توابع کمکی برای محاسبه هزینه
# ═══════════════════════════════════════════════════════════

async def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> int:
    """محاسبه هزینه بر اساس توکن مصرفی (تومان)"""
    config = await get_ai_config(model_name)
    if not config:
        # مقادیر پیش‌فرض
        input_price = 22.5  # تومان per 1K
        output_price = 90   # تومان per 1K
    else:
        input_price = config.get("input_price_per_1k", 22.5)
        output_price = config.get("output_price_per_1k", 90)
    
    cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
    return int(cost) + 1  # گرد به بالا


async def process_ai_request(telegram_id: int, model_name: str,
                             input_tokens: int, output_tokens: int) -> dict:
    """
    پردازش درخواست AI با کسر اعتبار
    Returns: {"success": bool, "cost": int, "new_balance": int, "error": str?}
    """
    # محاسبه هزینه
    cost = await calculate_cost(model_name, input_tokens, output_tokens)
    
    # بررسی و کسر اعتبار
    new_balance = await deduct_credit(telegram_id, cost)
    
    if new_balance is None:
        current = await get_user_credit(telegram_id)
        return {
            "success": False,
            "cost": cost,
            "current_balance": current,
            "error": "اعتبار کافی نیست"
        }
    
    # ثبت تراکنش
    await create_transaction(
        user_telegram_id=telegram_id,
        trans_type="usage",
        amount=-cost,
        description=f"استفاده از {model_name}",
        ai_model=model_name,
        tokens_used=input_tokens + output_tokens
    )
    
    return {
        "success": True,
        "cost": cost,
        "new_balance": new_balance
    }


# ═══════════════════════════════════════════════════════════
# تست اتصال
# ═══════════════════════════════════════════════════════════

async def test_connection() -> bool:
    """تست اتصال به NocoDB"""
    try:
        packages = await get_active_packages()
        print(f"✅ اتصال برقرار! {len(packages)} بسته فعال یافت شد.")
        for pkg in packages:
            print(f"   📦 {pkg.get('name')}: {pkg.get('price'):,} تومان → {pkg.get('credit'):,} اعتبار")
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())

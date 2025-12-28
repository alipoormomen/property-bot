# nocodb_client.py
"""
NocoDB Client for PropertyBot
Handles all database operations with NocoDB API
"""

import os
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# تنظیمات اتصال
# ============================================================

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

# Table IDs از خروجی setup
TABLE_IDS = {
    "users": "m2exwsn2lm2scg7",
    "properties": "mwgik4tnx5fdrls",
    "transactions": "mn0clzygu0ex3lq",
    "packages": "mbgg7z5f3uv36jd",
    "ai_config": "mea2jyex8qolo6t",
}

HEADERS = {
    "xc-token": NOCODB_TOKEN,
    "Content-Type": "application/json"
}


# ============================================================
# توابع پایه API
# ============================================================

async def _request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """ارسال درخواست به NocoDB API"""
    url = f"{NOCODB_URL}/api/v2{endpoint}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        if method == "GET":
            response = await client.get(url, headers=HEADERS, params=data)
        elif method == "POST":
            response = await client.post(url, headers=HEADERS, json=data)
        elif method == "PATCH":
            response = await client.patch(url, headers=HEADERS, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=HEADERS)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        if response.status_code >= 400:
            raise Exception(f"NocoDB Error {response.status_code}: {response.text}")
        
        return response.json() if response.text else {}


def _table_url(table: str) -> str:
    """ساخت URL برای جدول"""
    return f"/tables/{TABLE_IDS[table]}/records"


# ============================================================
# 👤 مدیریت کاربران (users)
# ============================================================

async def get_user(telegram_id: int) -> Optional[Dict]:
    """دریافت کاربر با telegram_id"""
    endpoint = _table_url("users")
    params = {"where": f"(telegram_id,eq,{telegram_id})"}
    
    result = await _request("GET", endpoint, params)
    records = result.get("list", [])
    
    return records[0] if records else None


async def create_user(
    telegram_id: int,
    phone: str = None,
    first_name: str = None,
    username: str = None,
    initial_credit: int = 5000  # اعتبار اولیه رایگان
) -> Dict:
    """ساخت کاربر جدید"""
    data = {
        "telegram_id": telegram_id,
        "phone": phone,
        "first_name": first_name,
        "username": username,
        "credit_balance": initial_credit,
        "total_spent": 0,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    return await _request("POST", _table_url("users"), data)


async def get_or_create_user(telegram_id: int, **kwargs) -> Dict:
    """دریافت یا ساخت کاربر"""
    user = await get_user(telegram_id)
    if user:
        return user
    return await create_user(telegram_id, **kwargs)


async def update_user_credit(telegram_id: int, amount: int, operation: str = "subtract") -> Dict:
    """
    بروزرسانی اعتبار کاربر
    operation: 'subtract' برای کم کردن، 'add' برای اضافه کردن
    """
    user = await get_user(telegram_id)
    if not user:
        raise Exception(f"User {telegram_id} not found")
    
    current = user.get("credit_balance", 0)
    
    if operation == "subtract":
        new_balance = max(0, current - amount)
        new_spent = user.get("total_spent", 0) + amount
    else:  # add
        new_balance = current + amount
        new_spent = user.get("total_spent", 0)
    
    row_id = user["Id"]
    endpoint = f"{_table_url('users')}/{row_id}"
    
    data = {
        "credit_balance": new_balance,
        "total_spent": new_spent,
        "updated_at": datetime.now().isoformat()
    }
    
    return await _request("PATCH", endpoint, data)


async def check_user_credit(telegram_id: int, required: int) -> bool:
    """بررسی کافی بودن اعتبار"""
    user = await get_user(telegram_id)
    if not user:
        return False
    return user.get("credit_balance", 0) >= required


async def update_user_phone(telegram_id: int, phone: str) -> Dict:
    """بروزرسانی شماره موبایل"""
    user = await get_user(telegram_id)
    if not user:
        raise Exception(f"User {telegram_id} not found")
    
    row_id = user["Id"]
    endpoint = f"{_table_url('users')}/{row_id}"
    
    data = {
        "phone": phone,
        "updated_at": datetime.now().isoformat()
    }
    
    return await _request("PATCH", endpoint, data)


# ============================================================
# 🏠 مدیریت املاک (properties)
# ============================================================

async def create_property(
    telegram_id: int,
    raw_text: str,
    extracted_data: Dict,
    ai_tokens_used: int = 0,
    ai_cost: int = 0
) -> Dict:
    """ثبت ملک جدید"""
    data = {
        "user_id": telegram_id,
        "raw_text": raw_text,
        "property_type": extracted_data.get("property_type"),
        "transaction_type": extracted_data.get("transaction_type"),
        "city": extracted_data.get("city"),
        "neighborhood": extracted_data.get("neighborhood"),
        "area": extracted_data.get("area"),
        "rooms": extracted_data.get("rooms"),
        "price": extracted_data.get("price"),
        "price_per_meter": extracted_data.get("price_per_meter"),
        "deposit": extracted_data.get("deposit"),
        "rent": extracted_data.get("rent"),
        "features": ",".join(extracted_data.get("features", [])),
        "floor": extracted_data.get("floor"),
        "total_floors": extracted_data.get("total_floors"),
        "year_built": extracted_data.get("year_built"),
        "extracted_json": str(extracted_data),
        "ai_tokens_used": ai_tokens_used,
        "ai_cost": ai_cost,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    
    return await _request("POST", _table_url("properties"), data)


async def get_user_properties(telegram_id: int, limit: int = 10) -> List[Dict]:
    """دریافت املاک کاربر"""
    endpoint = _table_url("properties")
    params = {
        "where": f"(user_id,eq,{telegram_id})",
        "sort": "-created_at",
        "limit": limit
    }
    
    result = await _request("GET", endpoint, params)
    return result.get("list", [])


async def get_property(property_id: int) -> Optional[Dict]:
    """دریافت یک ملک با ID"""
    endpoint = f"{_table_url('properties')}/{property_id}"
    
    try:
        return await _request("GET", endpoint)
    except:
        return None


async def update_property_status(property_id: int, status: str) -> Dict:
    """بروزرسانی وضعیت ملک"""
    endpoint = f"{_table_url('properties')}/{property_id}"
    data = {"status": status}
    
    return await _request("PATCH", endpoint, data)


# ============================================================
# 💳 مدیریت تراکنش‌ها (transactions)
# ============================================================

async def create_transaction(
    telegram_id: int,
    tx_type: str,  # 'usage' | 'purchase' | 'bonus' | 'refund'
    amount: int,
    description: str,
    property_id: int = None,
    package_id: int = None,
    ai_model: str = None,
    tokens_used: int = None
) -> Dict:
    """ثبت تراکنش جدید"""
    data = {
        "user_id": telegram_id,
        "type": tx_type,
        "amount": amount,
        "description": description,
        "property_id": property_id,
        "package_id": package_id,
        "ai_model": ai_model,
        "tokens_used": tokens_used,
        "created_at": datetime.now().isoformat(),
    }
    
    return await _request("POST", _table_url("transactions"), data)


async def get_user_transactions(telegram_id: int, limit: int = 20) -> List[Dict]:
    """دریافت تراکنش‌های کاربر"""
    endpoint = _table_url("transactions")
    params = {
        "where": f"(user_id,eq,{telegram_id})",
        "sort": "-created_at",
        "limit": limit
    }
    
    result = await _request("GET", endpoint, params)
    return result.get("list", [])


# ============================================================
# 📦 مدیریت بسته‌ها (packages)
# ============================================================

async def get_all_packages(active_only: bool = True) -> List[Dict]:
    """دریافت لیست بسته‌ها"""
    endpoint = _table_url("packages")
    params = {"sort": "price"}
    
    if active_only:
        params["where"] = "(is_active,eq,true)"
    
    result = await _request("GET", endpoint, params)
    return result.get("list", [])


async def get_package(package_id: int) -> Optional[Dict]:
    """دریافت یک بسته"""
    endpoint = f"{_table_url('packages')}/{package_id}"
    
    try:
        return await _request("GET", endpoint)
    except:
        return None


# ============================================================
# ⚙️ تنظیمات AI (ai_config)
# ============================================================

async def get_ai_config(model_name: str) -> Optional[Dict]:
    """دریافت تنظیمات یک مدل AI"""
    endpoint = _table_url("ai_config")
    params = {"where": f"(model_name,eq,{model_name})"}
    
    result = await _request("GET", endpoint, params)
    records = result.get("list", [])
    
    return records[0] if records else None


async def get_all_ai_configs() -> List[Dict]:
    """دریافت همه تنظیمات AI"""
    endpoint = _table_url("ai_config")
    result = await _request("GET", endpoint)
    return result.get("list", [])


async def calculate_ai_cost(model_name: str, input_tokens: int, output_tokens: int = 0) -> int:
    """محاسبه هزینه AI بر اساس توکن‌ها"""
    config = await get_ai_config(model_name)
    
    if not config:
        # fallback به نرخ پیش‌فرض
        return int((input_tokens + output_tokens) * 0.1)
    
    input_cost = (input_tokens / 1000) * config.get("input_price_per_1k", 0)
    output_cost = (output_tokens / 1000) * config.get("output_price_per_1k", 0)
    
    return int(input_cost + output_cost)


# ============================================================
# 🔧 توابع کمکی
# ============================================================

async def log_ai_usage(
    telegram_id: int,
    model: str,
    input_tokens: int,
    output_tokens: int,
    property_id: int = None,
    description: str = None
) -> int:
    """
    ثبت مصرف AI و کم کردن اعتبار
    Returns: هزینه کسر شده
    """
    # محاسبه هزینه
    cost = await calculate_ai_cost(model, input_tokens, output_tokens)
    
    # کم کردن از اعتبار
    await update_user_credit(telegram_id, cost, "subtract")
    
    # ثبت تراکنش
    await create_transaction(
        telegram_id=telegram_id,
        tx_type="usage",
        amount=-cost,
        description=description or f"استفاده از {model}",
        property_id=property_id,
        ai_model=model,
        tokens_used=input_tokens + output_tokens
    )
    
    return cost


async def purchase_package(telegram_id: int, package_id: int) -> Dict:
    """
    خرید بسته اعتباری
    Returns: اطلاعات خرید
    """
    package = await get_package(package_id)
    if not package:
        raise Exception("بسته پیدا نشد")
    
    if not package.get("is_active"):
        raise Exception("این بسته غیرفعال است")
    
    credit_amount = package["credit_amount"]
    bonus = package.get("bonus_percent", 0)
    total_credit = int(credit_amount * (1 + bonus / 100))
    
    # اضافه کردن اعتبار
    await update_user_credit(telegram_id, total_credit, "add")
    
    # ثبت تراکنش
    await create_transaction(
        telegram_id=telegram_id,
        tx_type="purchase",
        amount=total_credit,
        description=f"خرید بسته {package['name']}",
        package_id=package_id
    )
    
    return {
        "package": package,
        "credit_added": total_credit,
        "bonus_applied": bonus
    }


# ============================================================
# 🧪 تست اتصال
# ============================================================

async def test_connection() -> bool:
    """تست اتصال به NocoDB"""
    try:
        packages = await get_all_packages()
        print(f"✅ اتصال برقرار! {len(packages)} بسته یافت شد.")
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False


# برای تست مستقیم
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())

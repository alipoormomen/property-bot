"""
NocoDB Client - ماژول ارتباط با دیتابیس
Facade Layer
"""

import os
import httpx
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# ✅ سیستم اعتبار جدید (Core)
from services.nocodb.credit import (
    get_user_balance,
    charge_credit,
    consume_credit,
)

load_dotenv()

# ═══════════════════════════════════════════════════════════
# تنظیمات اتصال
# ═══════════════════════════════════════════════════════════

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

TABLES = {
    "users": "m2exwsn2lm2scg7",
    "properties": "mwgik4tnx5fdrls",
    "transactions": "mn0clzygu0ex3lq",
    "packages": "mv3d40e9u4xlmi2",
    "ai_config": "mea2jyex8qolo6t",
}

# ═══════════════════════════════════════════════════════════

def _headers():
    return {"xc-token": NOCODB_TOKEN}


def _table_url(table_name: str) -> str:
    table_id = TABLES.get(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found")
    return f"{NOCODB_URL}/api/v2/tables/{table_id}/records"


# ═══════════════════════════════════════════════════════════
# کاربران
# ═══════════════════════════════════════════════════════════

async def get_user(telegram_id: int) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _table_url("users"),
            headers=_headers(),
            params={"where": f"(telegram_id,eq,{telegram_id})"},
        )
        if resp.status_code == 200:
            records = resp.json().get("list", [])
            return records[0] if records else None
    return None


async def create_user(
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    phone: str = None,
) -> dict:
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "phone": phone,
        "balance": 0,
        "total_charged": 0,
        "total_used": 0,
        "is_active": 1,
        "created_at": datetime.now().isoformat(),
    }

    async with httpx.AsyncClient() as client:
        await client.post(_table_url("users"), headers=_headers(), json=payload)

    return await get_user(telegram_id)


async def get_or_create_user(telegram_id: int, **kwargs) -> dict:
    return await get_user(telegram_id) or await create_user(telegram_id, **kwargs)


# ═══════════════════════════════════════════════════════════
# ✅ Facade سیستم اعتبار (سازگار با کدهای قبلی)
# ═══════════════════════════════════════════════════════════

async def get_user_credit(telegram_id: int) -> int:
    return await get_user_balance(telegram_id)


async def add_credit(telegram_id: int, amount: int) -> int:
    return await charge_credit(
        telegram_id=telegram_id,
        amount=amount,
        description="شارژ دستی",
    )

async def refund_credit(
    telegram_id: int,
    amount: int,
    reason: str,
    ref_transaction_id: str,
):
    return await charge_credit(
        telegram_id=telegram_id,
        amount=-abs(amount),
        description=reason,
        ref_transaction_id=ref_transaction_id,
    )

async def deduct_credit(telegram_id: int, amount: int) -> Optional[int]:
    result = await consume_credit(
        telegram_id=telegram_id,
        amount=amount,
        description="کسر اعتبار",
    )
    return result["new_balance"] if result["success"] else None


# ═══════════════════════════════════════════════════════════
# املاک (create_property همان نسخه تأییدشده قبلی شماست)
# ═══════════════════════════════════════════════════════════

async def create_property(user_telegram_id: int, payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _table_url("properties"),
            headers=_headers(),
            json={k: v for k, v in payload.items() if v is not None},
        )
        resp.raise_for_status()
        return resp.json()


# ═══════════════════════════════════════════════════════════
# تراکنش‌ها
# ═══════════════════════════════════════════════════════════

async def create_transaction(**payload) -> dict:
    payload["created_at"] = datetime.now().isoformat()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _table_url("transactions"),
            headers=_headers(),
            json={k: v for k, v in payload.items() if v is not None},
        )
        resp.raise_for_status()
        return resp.json() if resp.text else {"status": "created"}


# ═══════════════════════════════════════════════════════════
# بسته‌ها و AI Config
# ═══════════════════════════════════════════════════════════

async def get_active_packages() -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _table_url("packages"),
            headers=_headers(),
            params={"where": "(is_active,eq,1)"},
        )
        return resp.json().get("list", []) if resp.status_code == 200 else []


async def get_ai_config(model_name: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _table_url("ai_config"),
            headers=_headers(),
            params={"where": f"(model_name,eq,{model_name})"},
        )
        if resp.status_code == 200:
            items = resp.json().get("list", [])
            return items[0] if items else None
    return None


# ═══════════════════════════════════════════════════════════
# ✅ پردازش درخواست AI (کاملاً متصل به credit جدید)
# ═══════════════════════════════════════════════════════════

async def process_ai_request(
    telegram_id: int,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:

    cost = int((input_tokens * 0.0225 + output_tokens * 0.09) / 1000) + 1

    result = await consume_credit(
        telegram_id=telegram_id,
        amount=cost,
        description=f"AI usage: {model_name}",
        ai_model=model_name,
        tokens_used=input_tokens + output_tokens,
    )

    if not result["success"]:
        return {
            "success": False,
            "cost": cost,
            "current_balance": result["current_balance"],
            "error": "اعتبار کافی نیست",
        }

    return {
        "success": True,
        "cost": cost,
        "new_balance": result["new_balance"],
    }


# ═══════════════════════════════════════════════════════════
# تست
# ═══════════════════════════════════════════════════════════

async def test_connection():
    packages = await get_active_packages()
    print(f"✅ اتصال برقرار – {len(packages)} بسته فعال")
    for p in packages:
        print(f"📦 {p.get('name')} → {p.get('credits',0)} اعتبار")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())

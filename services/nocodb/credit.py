"""
Credit Management System
مدیریت اعتبار کاربران
"""

from .users import get_user_by_telegram_id
from .transactions import create_transaction
from .base import get_client
from .tables import USERS_TABLE_ID


async def get_user_balance(telegram_id: int) -> int:
    """دریافت موجودی فعلی کاربر"""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return 0
    return int(user.get("balance", 0) or 0)


async def charge_credit(
    telegram_id: int,
    amount: int,
    description: str = "manual charge",
    ref_transaction_id: str = None,  # ✅ اضافه شد
) -> int:
    """
    شارژ اعتبار کاربر
    Returns: موجودی جدید
    """
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        raise ValueError(f"User {telegram_id} not found")

    user_id = user["Id"]
    current_balance = int(user.get("balance", 0) or 0)
    new_balance = current_balance + amount

    # بروزرسانی موجودی
    async with get_client() as client:
        res = await client.patch(
            f"/tables/{USERS_TABLE_ID}/records",
            json={"Id": user_id, "balance": new_balance}
        )
        res.raise_for_status()

    # ثبت تراکنش
    tx_payload = {
        "user_id": telegram_id,
        "amount": amount,
        "type": "charge" if amount > 0 else "refund",
        "description": description,
        "balance_after": new_balance,
    }
    
    # ✅ اضافه کردن ref_transaction_id اگر وجود داشت
    if ref_transaction_id:
        tx_payload["reference_id"] = ref_transaction_id
    
    await create_transaction(tx_payload)

    return new_balance


async def consume_credit(
    telegram_id: int,
    amount: int,
    description: str = "usage",
    ai_model: str = None,
    tokens_used: int = None,
) -> dict:
    """
    مصرف اعتبار
    Returns: {"success": bool, "current_balance": int, "new_balance": int}
    """
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return {"success": False, "current_balance": 0, "new_balance": 0}

    user_id = user["Id"]
    current_balance = int(user.get("balance", 0) or 0)

    if current_balance < amount:
        return {
            "success": False,
            "current_balance": current_balance,
            "new_balance": current_balance,
        }

    new_balance = current_balance - amount

    # بروزرسانی موجودی
    async with get_client() as client:
        res = await client.patch(
            f"/tables/{USERS_TABLE_ID}/records",
            json={"Id": user_id, "balance": new_balance}
        )
        res.raise_for_status()

    # ثبت تراکنش
    tx_payload = {
        "user_id": telegram_id,
        "amount": -amount,
        "type": "consume",
        "description": description,
        "balance_after": new_balance,
    }
    
    # ✅ اضافه کردن اطلاعات AI اگر وجود داشت
    if ai_model:
        tx_payload["ai_model"] = ai_model
    if tokens_used:
        tx_payload["tokens_used"] = tokens_used
    
    await create_transaction(tx_payload)

    return {
        "success": True,
        "current_balance": current_balance,
        "new_balance": new_balance,
    }

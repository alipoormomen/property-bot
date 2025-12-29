from .users import get_user_by_telegram_id
from .transactions import create_transaction
from .base import get_client

class InsufficientCredit(Exception):
    pass


async def get_user_balance(telegram_id: int) -> int:
    user = await get_user_by_telegram_id(telegram_id)
    return user.get("balance", 0) if user else 0


async def charge_credit(
    telegram_id: int,
    amount: int,
    description: str = "manual charge"
):
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        raise ValueError("User not found")

    before = user.get("balance", 0)
    after = before + amount

    async with get_client() as client:
        await client.patch(
            "/tables/users/records",
            json={
                "Id": user["Id"],
                "balance": after,
                "total_charged": (user.get("total_charged") or 0) + amount
            }
        )

    await create_transaction({
        "type": "charge",
        "amount": amount,
        "balance_before": before,
        "balance_after": after,
        "description": description,
        "user_telegram_id": telegram_id
    })


async def consume_credit(
    telegram_id: int,
    amount: int,
    description: str
):
    if amount <= 0:
        return

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        raise ValueError("User not found")

    before = user.get("balance", 0)
    if before < amount:
        raise InsufficientCredit()

    after = before - amount

    async with get_client() as client:
        await client.patch(
            "/tables/users/records",
            json={
                "Id": user["Id"],
                "balance": after,
                "total_used": (user.get("total_used") or 0) + amount
            }
        )

    await create_transaction({
        "type": "usage",
        "amount": amount,
        "balance_before": before,
        "balance_after": after,
        "description": description,
        "user_telegram_id": telegram_id
    })

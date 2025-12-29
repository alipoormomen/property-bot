from .base import get_client

USERS_TABLE = "users"


async def get_user_by_telegram_id(telegram_id: int):
    async with get_client() as client:
        res = await client.get(
            f"/tables/{USERS_TABLE}/records",
            params={"where": f"(telegram_id,eq,{telegram_id})", "limit": 1}
        )
        res.raise_for_status()
        data = res.json().get("list", [])
        return data[0] if data else None

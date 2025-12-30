from .base import get_client

USERS_TABLE = "m2exwsn2lm2scg7"

async def get_user_by_telegram_id(telegram_id: int):
    url = f"{BASE_URL}/api/v2/tables/{USERS_TABLE}/records"

    params = {
        "where": f"(telegram_id,eq,{telegram_id})",
        "limit": 1
    }

    res = await client.get(url, params=params)
    res.raise_for_status()

    data = res.json().get("list", [])
    return data[0] if data else None



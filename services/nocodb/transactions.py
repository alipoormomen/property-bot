from datetime import datetime
from .base import get_client
from .tables import TRANSACTIONS_TABLE_ID


async def create_transaction(payload: dict):
    async with get_client() as client:
        res = await client.post(
            f"/tables/{TRANSACTIONS_TABLE_ID}/records",
            json={
                **payload,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        res.raise_for_status()
        return res.json()

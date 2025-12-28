# debug_tx_type.py
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    url = f"{os.getenv('NOCODB_URL')}/api/v2/tables/mwgik4tnx5fdrls/records"
    headers = {"xc-token": os.getenv("NOCODB_TOKEN")}
    
    # تست با transaction_type فارسی
    payload = {
        "user_telegram_id": 123,
        "property_type": "apartment",
        "transaction_type": "فروش"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

asyncio.run(main())

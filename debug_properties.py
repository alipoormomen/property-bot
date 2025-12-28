# debug_properties.py
import asyncio
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")
PROPERTIES_TABLE_ID = "mwgik4tnx5fdrls"

async def main():
    print("🔍 بررسی ساختار جدول properties...\n")
    
    async with httpx.AsyncClient() as client:
        # 1. گرفتن رکوردهای موجود
        url = f"{NOCODB_URL}/api/v2/tables/{PROPERTIES_TABLE_ID}/records"
        headers = {"xc-token": NOCODB_TOKEN}
        
        resp = await client.get(url, headers=headers, params={"limit": 1})
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        
        # 2. تست با payload ساده
        print("\n📝 تست درج ساده...")
        simple_payload = {
            "user_telegram_id": 123456,
            "property_type": "آپارتمان"
        }
        
        resp2 = await client.post(url, headers=headers, json=simple_payload)
        print(f"Status: {resp2.status_code}")
        print(f"Response: {resp2.text}")
        
        if resp2.status_code != 200:
            # 3. تست با یک فیلد
            print("\n📝 تست با فقط یک فیلد...")
            resp3 = await client.post(url, headers=headers, json={"property_type": "تست"})
            print(f"Status: {resp3.status_code}")
            print(f"Response: {resp3.text}")

asyncio.run(main())

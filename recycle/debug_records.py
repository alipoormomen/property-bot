# debug_records.py
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

TABLES = {
    "users": "m2exwsn2lm2scg7",
    "properties": "mwgik4tnx5fdrls", 
    "transactions": "mn0clzygu0ex3lq",
}

async def check_all_records():
    headers = {"xc-token": NOCODB_TOKEN}
    
    async with httpx.AsyncClient() as client:
        print("=" * 50)
        
        # بررسی Properties
        url = f"{NOCODB_URL}/api/v2/tables/{TABLES['properties']}/records"
        resp = await client.get(url, headers=headers)
        data = resp.json()
        print(f"🏠 Properties: {len(data.get('list', []))} رکورد")
        for p in data.get('list', [])[:3]:
            print(f"   - user: {p.get('user_telegram_id')} | type: {p.get('property_type')}")
        
        print("-" * 50)
        
        # بررسی Transactions  
        url = f"{NOCODB_URL}/api/v2/tables/{TABLES['transactions']}/records"
        resp = await client.get(url, headers=headers)
        data = resp.json()
        print(f"📜 Transactions: {len(data.get('list', []))} رکورد")
        for t in data.get('list', [])[:3]:
            print(f"   - user: {t.get('user_telegram_id')} | type: {t.get('type')} | amount: {t.get('amount')}")
        
        print("-" * 50)
        
        # بررسی Users
        url = f"{NOCODB_URL}/api/v2/tables/{TABLES['users']}/records"
        resp = await client.get(url, headers=headers)
        data = resp.json()
        print(f"👤 Users: {len(data.get('list', []))} رکورد")
        for u in data.get('list', [])[:3]:
            print(f"   - telegram_id: {u.get('telegram_id')} | balance: {u.get('balance')}")

asyncio.run(check_all_records())

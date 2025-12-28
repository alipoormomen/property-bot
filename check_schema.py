# check_schema.py
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

TABLES = {
    "properties": "mwgik4tnx5fdrls", 
    "transactions": "mn0clzygu0ex3lq",
}

async def check_schema():
    headers = {"xc-token": NOCODB_TOKEN}
    
    async with httpx.AsyncClient() as client:
        for name, table_id in TABLES.items():
            print(f"\n{'='*50}")
            print(f"📋 {name.upper()} - Schema:")
            print(f"{'='*50}")
            
            # دریافت یک رکورد برای دیدن فیلدها
            url = f"{NOCODB_URL}/api/v2/tables/{table_id}/records"
            resp = await client.get(url, headers=headers, params={"limit": 1})
            data = resp.json()
            
            if data.get('list'):
                record = data['list'][0]
                for key, value in record.items():
                    print(f"   {key}: {value}")
            else:
                print("   (خالی)")

asyncio.run(check_schema())

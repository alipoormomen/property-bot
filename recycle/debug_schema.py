# debug_schema.py
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

def _headers():
    return {"xc-token": NOCODB_TOKEN}

async def check_table_schema():
    async with httpx.AsyncClient() as client:
        for name, table_id in TABLES.items():
            print(f"\n{'='*60}")
            print(f"📋 جدول: {name} (ID: {table_id})")
            print("="*60)
            
            # دریافت یک رکورد نمونه
            url = f"{NOCODB_URL}/api/v2/tables/{table_id}/records"
            params = {"limit": 3}
            resp = await client.get(url, headers=_headers(), params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("list", [])
                print(f"تعداد رکوردها (نمونه): {len(records)}")
                
                if records:
                    print("\n🔑 فیلدهای موجود و مقادیر نمونه:")
                    for key, value in records[0].items():
                        print(f"   • {key}: {value} (type: {type(value).__name__})")
                else:
                    print("❌ هیچ رکوردی یافت نشد")
            else:
                print(f"❌ خطا: {resp.status_code}")
                print(resp.text[:500])

asyncio.run(check_table_schema())

# find_base_id.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

headers = {"xc-token": NOCODB_TOKEN}

# لیست همه bases
resp = httpx.get(f"{NOCODB_URL}/api/v2/meta/bases", headers=headers)

if resp.status_code == 200:
    data = resp.json()
    bases = data.get("list", [])
    print(f"✅ {len(bases)} پایگاه داده یافت شد:\n")
    for base in bases:
        print(f"   📁 {base.get('title', 'N/A')}")
        print(f"      ID: {base.get('id')}")
        print()
else:
    print(f"❌ خطا: {resp.status_code}")
    print(resp.text)

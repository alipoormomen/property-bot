# get_new_table_id.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

headers = {"xc-token": NOCODB_TOKEN}

resp = httpx.get(
    f"{NOCODB_URL}/api/v2/meta/bases/p1lsnufyyyjcf1p/tables",
    headers=headers
)

for t in resp.json().get("list", []):
    print(f"{t['title']}: {t['id']}")

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load .env file
load_dotenv()

NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")
NOCODB_URL = os.getenv("NOCODB_URL")

if not NOCODB_TOKEN or not NOCODB_URL:
    raise RuntimeError("NOCODB_TOKEN یا NOCODB_URL ست نشده است")

headers = {"xc-token": NOCODB_TOKEN}


async def fetch_bases(client):
    r = await client.get(
        f"{NOCODB_URL}/api/v1/db/meta/projects",
        headers=headers
    )
    r.raise_for_status()
    return r.json().get("list", [])


async def fetch_tables(client, base_id):
    r = await client.get(
        f"{NOCODB_URL}/api/v1/db/meta/projects/{base_id}/tables",
        headers=headers
    )
    r.raise_for_status()
    return r.json().get("list", [])


async def fetch_columns(client, base_id, table):
    table_id = table["id"]

    r = await client.get(
        f"{NOCODB_URL}/api/v1/db/data/v1/{base_id}/{table_id}/describe",
        headers=headers
    )

    if r.status_code in (404, 422):
        return None

    r.raise_for_status()
    return r.json().get("list", [])





async def main():
    async with httpx.AsyncClient(timeout=10) as client:
        bases = await fetch_bases(client)

        for base in bases:
            print(f"\n📦 Base: {base['title']} ({base['id']})")

            tables = await fetch_tables(client, base["id"])
            for table in tables:
                print(f"\n  🧱 Table: {table['title']} ({table['id']})")

                columns = await fetch_columns(client, base["id"], table)

                if not columns:
                    print("    ⚠️ No columns (view or system table)")
                    continue

                for col in columns:
                    print(
                        f"    - {col['title']} | {col['uidt']} | "
                        f"required={col.get('required', False)}"
                    )



if __name__ == "__main__":
    asyncio.run(main())

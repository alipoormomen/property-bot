import asyncio

from .base import get_client
from .tables import USERS_TABLE_ID


COLUMNS = [
    {
        "title": "telegram_id",
        "uidt": "Number"
    },
    {
        "title": "username",
        "uidt": "SingleLineText"
    },
    {
        "title": "first_name",
        "uidt": "SingleLineText"
    },
    {
        "title": "last_name",
        "uidt": "SingleLineText"
    },
    {
        "title": "credit",
        "uidt": "Number",
        "default": 0
    },
    {
        "title": "is_admin",
        "uidt": "Checkbox",
        "default": False
    }
]


async def main():
    async with get_client() as client:
        for col in COLUMNS:
            res = await client.post(
                f"/meta/tables/{USERS_TABLE_ID}/columns",
                json=col
            )

            if res.status_code not in (200, 201):
                print(f"❌ Error creating column '{col['title']}': {res.text}")
            else:
                print(f"✅ Created column: {col['title']}")


if __name__ == "__main__":
    asyncio.run(main())

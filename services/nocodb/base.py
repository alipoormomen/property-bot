import httpx
from config import NOCODB_URL, NOCODB_TOKEN


def get_client():
    return httpx.AsyncClient(
        base_url=f"{NOCODB_URL}/api/v2",
        headers={
            "Authorization": f"Bearer {NOCODB_TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=30
    )

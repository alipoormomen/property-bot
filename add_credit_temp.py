import httpx
from config import NOCODB_URL, NOCODB_TOKEN

USERS_TABLE_ID = "m2exwsn2lm2scg7"

TELEGRAM_ID = 41676077
ADD_CREDIT_AMOUNT = 1000

HEADERS = {
    "xc-token": NOCODB_TOKEN,
    "Content-Type": "application/json",
}


def get_user_by_telegram_id(client):
    res = client.get(
        f"{NOCODB_URL}/api/v2/tables/{USERS_TABLE_ID}/records",
        headers=HEADERS,
        params={
            "where": f"(telegram_id,eq,{TELEGRAM_ID})",
            "limit": 1,
        },
    )
    res.raise_for_status()

    data = res.json().get("list", [])
    if not data:
        return None

    return data[0]


def create_user(client):
    res = client.post(
        f"{NOCODB_URL}/api/v2/tables/{USERS_TABLE_ID}/records",
        headers=HEADERS,
        json=[
            {
                "telegram_id": TELEGRAM_ID,
                "username": "test_user",
                "first_name": "Test",
                "last_name": "User",
                "credit": 0,
                "is_admin": False,
            }
        ],
    )
    res.raise_for_status()
    print("✅ User created")


def update_user_credit(client, record_id, new_credit):
    res = client.patch(
        f"{NOCODB_URL}/api/v2/tables/{USERS_TABLE_ID}/records",
        headers=HEADERS,
        json=[
            {
                "Id": record_id,
                "credit": new_credit,
            }
        ],
    )
    res.raise_for_status()
    print("✅ Credit updated")


def delete_user(client, record_id):
    res = client.delete(
        f"{NOCODB_URL}/api/v2/tables/{USERS_TABLE_ID}/records",
        headers=HEADERS,
        params={"ids": record_id},
    )
    res.raise_for_status()
    print("🗑 User deleted")


def main():
    with httpx.Client(timeout=30) as client:
        user = get_user_by_telegram_id(client)

        if user is None:
            print("ℹ User not found → creating test user")
            create_user(client)
            user = get_user_by_telegram_id(client)

        print("USER JSON:", user)

        record_id = user["Id"]
        current_credit = user.get("credit", 0)

        new_credit = current_credit + ADD_CREDIT_AMOUNT
        update_user_credit(client, record_id, new_credit)

        # ✅ اگر خواستی حذف را تست کنی، این خط را باز کن
        # delete_user(client, record_id)


if __name__ == "__main__":
    main()

import httpx

# ================= CONFIG =================

NOCODB_URL = "http://localhost:8080"
NOCODB_TOKEN = "AfU3D9flJQds51QS3myvmVmbzEIypXqPFpLcTOYd"

PROJECT_NAME = "PropertyBot"   # اگر اسم پروژه فرق دارد، اصلاح کن
TABLE_NAME = "users"

TELEGRAM_ID = 41676077
ADD_CREDIT_AMOUNT = 10   # مثلا 10 کردیت ویژه
# ==========================================


HEADERS = {
    "xc-token": NOCODB_TOKEN,
    "Content-Type": "application/json"
}


def get_user_by_telegram_id(client):
    url = f"{NOCODB_URL}/api/v1/db/data/v1/{PROJECT_NAME}/{TABLE_NAME}"
    params = {
        "where": f"(telegram_id,eq,{TELEGRAM_ID})"
    }
    r = client.get(url, headers=HEADERS, params=params)
    r.raise_for_status()

    data = r.json()
    if not data.get("list"):
        raise Exception("❌ User not found")

    return data["list"][0]


def update_user_credit(client, user_id, new_credit):
    url = f"{NOCODB_URL}/api/v1/db/data/v1/{PROJECT_NAME}/{TABLE_NAME}/{user_id}"
    payload = {
        "credit": new_credit
    }
    r = client.patch(url, headers=HEADERS, json=payload)
    r.raise_for_status()


def main():
    with httpx.Client() as client:
        user = get_user_by_telegram_id(client)

        current_credit = user.get("credit", 0)
        new_credit = current_credit + ADD_CREDIT_AMOUNT

        update_user_credit(client, user["id"], new_credit)

        print("✅ Credit updated successfully")
        print(f"Telegram ID: {TELEGRAM_ID}")
        print(f"Old credit: {current_credit}")
        print(f"New credit: {new_credit}")


if __name__ == "__main__":
    main()

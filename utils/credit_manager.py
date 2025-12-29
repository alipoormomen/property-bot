import json
import os
from threading import Lock

CREDITS_FILE = "credits_store.json"
_lock = Lock()


def load_credits():
    if not os.path.exists(CREDITS_FILE):
        return {}
    with open(CREDITS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_credits(data):
    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_credit(user_id: int) -> int:
    with _lock:
        data = load_credits()
        return int(data.get(str(user_id), 0))


def set_user_credit(user_id: int, amount: int):
    with _lock:
        data = load_credits()
        data[str(user_id)] = amount
        save_credits(data)


def decrease_credit(user_id: int, amount: int = 1) -> bool:
    """
    returns True if credit deducted
    returns False if insufficient credit
    """
    with _lock:
        data = load_credits()
        uid = str(user_id)
        current = int(data.get(uid, 0))

        if current < amount:
            return False

        data[uid] = current - amount
        save_credits(data)
        return True

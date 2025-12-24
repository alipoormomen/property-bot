# main.py
# ✅ FIXED VERSION

from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ✅ FIX: خواندن token از .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN در فایل .env تنظیم نشده")


@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is running"}


@app.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    """
    Webhook endpoint برای دریافت پیام‌های تلگرام
    """
    data = await req.json()
    print(data)

    chat_id = data["message"]["chat"]["id"]
    send_message(chat_id, "✅ ویس شما دریافت شد (تست اولیه)")

    return {"ok": True}


def send_message(chat_id, text):
    """
    ارسال پیام به تلگرام
    ✅ FIX: استفاده از token از .env
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Error sending message: {response.text}")
    
    return response.json()

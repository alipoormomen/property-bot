# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ خواندن متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
AVALAIGPT_API_KEY = os.getenv("AVALAIGPT_API_KEY")  # ✅ تغییر نام
PROXY_URL = os.getenv("PROXY_URL")

# بررسی متغیرهای ضروری
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN در فایل .env تنظیم نشده")

if not AVALAIGPT_API_KEY:  # ✅ تغییر نام
    raise RuntimeError("❌ AVALAIGPT_API_KEY در فایل .env تنظیم نشده")

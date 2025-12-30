# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AVALAIGPT_API_KEY = os.getenv("AVALAIGPT_API_KEY")
PROXY_URL = os.getenv("PROXY_URL")  # ✅ برگشت

NOCODB_URL = os.getenv("NOCODB_URL")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN تنظیم نشده")

if not AVALAIGPT_API_KEY:
    raise RuntimeError("❌ AVALAIGPT_API_KEY تنظیم نشده")

if not NOCODB_URL or not NOCODB_TOKEN:
    raise RuntimeError("❌ NOCODB_URL یا NOCODB_TOKEN تنظیم نشده")

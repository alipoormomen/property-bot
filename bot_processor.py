# bot_processor.py - Main Processing Logic with Reply Keyboard Support
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes

from conversation_state import get_state, set_state, clear_state
from rule_engine import apply_rules
from extractor import extract_json as extract_property_info
from bot_utils import format_property_summary, normalize_yes_no, text_to_int
from services.inference_service import normalize_location

logger = logging.getLogger(__name__)

# ========================================
# 🎹 Reply Keyboard Options
# ========================================

KEYBOARD_OPTIONS = {
    "transaction_type": {
        "question": "نوع معامله را انتخاب کنید:",
        "buttons": [["🏷️ فروش", "🔑 رهن و اجاره"], ["🏗️ پیش‌فروش"]],
        "mapping": {
            "🏷️ فروش": "Sale", "فروش": "Sale",
            "🔑 رهن و اجاره": "Rent", "رهن و اجاره": "Rent", "رهن": "Rent", "اجاره": "Rent",
            "🏗️ پیش‌فروش": "Pre-sale", "پیش‌فروش": "Pre-sale", "پیش فروش": "Pre-sale"
        }
    },
    "property_type": {
        "question": "نوع ملک را انتخاب کنید:",
        "buttons": [["🏢 آپارتمان", "🏠 ویلا"], ["🏬 مغازه", "🌍 زمین"]],
        "mapping": {
            "🏢 آپارتمان": "Apartment", "آپارتمان": "Apartment",
            "🏠 ویلا": "Villa", "ویلا": "Villa",
            "🏬 مغازه": "Shop", "مغازه": "Shop",
            "🌍 زمین": "Land", "زمین": "Land"
        }
    },
    "usage_type": {
        "question": "نوع کاربری ملک را انتخاب کنید:",
        "buttons": [["🏠 مسکونی", "🏪 تجاری"], ["🏛️ اداری"]],
        "mapping": {
            "🏠 مسکونی": "Residential", "مسکونی": "Residential",
            "🏪 تجاری": "Commercial", "تجاری": "Commercial",
            "🏛️ اداری": "Administrative", "اداری": "Administrative"
        }
    },
    "has_elevator": {
        "question": "آیا ملک آسانسور دارد؟",
        "buttons": [["✅ بله", "❌ خیر"]],
        "mapping": {"✅ بله": True, "بله": True, "دارد": True, "❌ خیر": False, "خیر": False, "ندارد": False}
    },
    "has_parking": {
        "question": "آیا ملک پارکینگ دارد؟",
        "buttons": [["✅ بله", "❌ خیر"]],
        "mapping": {"✅ بله": True, "بله": True, "دارد": True, "❌ خیر": False, "خیر": False, "ندارد": False}
    },
    "has_storage": {
        "question": "آیا ملک انباری دارد؟",
        "buttons": [["✅ بله", "❌ خیر"]],
        "mapping": {"✅ بله": True, "بله": True, "دارد": True, "❌ خیر": False, "خیر": False, "ندارد": False}
    },
    "confirmation": {
        "question": "آیا اطلاعات صحیح است؟",
        "buttons": [["✅ تایید و ثبت", "✏️ ویرایش"], ["🗑️ لغو"]],
        "mapping": {
            "✅ تایید و ثبت": "confirm", "تایید": "confirm", "بله": "confirm",
            "✏️ ویرایش": "edit", "ویرایش": "edit",
            "🗑️ لغو": "cancel", "لغو": "cancel", "انصراف": "cancel"
        }
    }
}

# فیلدهای مورد نیاز
REQUIRED_FIELDS = {
    "base": ["transaction_type", "property_type", "area", "neighborhood", "city", "owner_name", "owner_phone"],
    "Apartment": ["bedroom_count", "floor", "total_floors", "has_elevator", "has_parking", "has_storage", "build_year"],
    "Villa": ["bedroom_count", "has_parking", "build_year"],
    "Shop": ["usage_type"],
    "Land": []
}

# سوالات متنی
TEXT_QUESTIONS = {
    "neighborhood": "📍 محله ملک را وارد کنید:",
    "city": "🏙️ شهر ملک را وارد کنید:",
    "area": "📐 متراژ ملک (متر مربع):",
    "bedroom_count": "🛏️ تعداد اتاق خواب:",
    "floor": "🏢 طبقه واحد:",
    "total_floors": "🏗️ تعداد کل طبقات:",
    "build_year": "📅 سال ساخت:",
    "price_total": "💰 قیمت کل (تومان):",
    "rent_mortgage": "💰 مبلغ رهن (تومان):",
    "rent_monthly": "📆 اجاره ماهیانه (تومان):",
    "owner_name": "👤 نام مالک:",
    "owner_phone": "📞 شماره تماس مالک:"
}

# ========================================
# 🔧 Helper Functions
# ========================================

def normalize_button_input(text: str, field: str):
    """تبدیل متن دکمه به مقدار سیستمی"""
    if field in KEYBOARD_OPTIONS:
        mapping = KEYBOARD_OPTIONS[field].get("mapping", {})
        if text in mapping:
            return mapping[text]
    return text

def get_reply_keyboard(field: str):
    """ساخت Reply Keyboard"""
    if field not in KEYBOARD_OPTIONS:
        return None
    buttons = KEYBOARD_OPTIONS[field]["buttons"]
    keyboard = [[KeyboardButton(btn) for btn in row] for row in buttons]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_question(field: str) -> str:
    """دریافت سوال"""
    if field in KEYBOARD_OPTIONS:
        return KEYBOARD_OPTIONS[field]["question"]
    return TEXT_QUESTIONS.get(field, f"لطفاً {field} را وارد کنید:")

def get_missing_fields(data: dict) -> list:
    """یافتن فیلدهای خالی"""
    missing = []
    
    for field in REQUIRED_FIELDS["base"]:
        if not data.get(field):
            missing.append(field)
    
    property_type = data.get("property_type")
    if property_type and property_type in REQUIRED_FIELDS:
        for field in REQUIRED_FIELDS[property_type]:
            if data.get(field) is None:
                missing.append(field)
    
    transaction = data.get("transaction_type")
    if transaction == "Sale" and not data.get("price_total"):
        missing.append("price_total")
    elif transaction == "Rent":
        if not data.get("rent_mortgage"):
            missing.append("rent_mortgage")
        if not data.get("rent_monthly"):
            missing.append("rent_monthly")
    
    return missing

# ========================================
# 📤 Response Functions
# ========================================

async def send_question(update: Update, field: str, prefix_message: str = None):
    """ارسال سوال"""
    question = get_question(field)
    keyboard = get_reply_keyboard(field)
    message = f"{prefix_message}\n\n{question}" if prefix_message else question
    
    if keyboard:
        await update.message.reply_text(message, reply_markup=keyboard)
    else:
        await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

async def send_summary(update: Update, data: dict):
    """ارسال خلاصه برای تایید"""
    summary = format_property_summary(data)
    keyboard = get_reply_keyboard("confirmation")
    await update.message.reply_text(
        f"📋 خلاصه اطلاعات ملک:\n\n{summary}\n\n{KEYBOARD_OPTIONS['confirmation']['question']}",
        reply_markup=keyboard
    )

# ========================================
# 🧠 Main Processing Logic
# ========================================

async def process_message(text: str, user_id: int, update: Update):
    """پردازش اصلی پیام کاربر"""
    
    state = get_state(user_id)
    data = state.get("data", {})
    waiting_for = state.get("waiting_for")
    
    logger.info(f"User {user_id}: text='{text}', waiting_for={waiting_for}")
    
    # ========== حالت ۱: منتظر پاسخ به سوال خاص ==========
    if waiting_for:
        value = normalize_button_input(text, waiting_for)
        
        # تبدیل مقادیر عددی
        if waiting_for in ["area", "bedroom_count", "floor", "total_floors", "build_year", "price_total", "rent_mortgage", "rent_monthly"]:
            value = text_to_int(text)
            if value is None:
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید.")
                return
        
        # ذخیره مقدار
        data[waiting_for] = value
        set_state(user_id, {"data": data, "waiting_for": None})
        
        # بررسی فیلدهای باقی‌مانده
        missing = get_missing_fields(data)
        
        if missing:
            next_field = missing[0]
            set_state(user_id, {"data": data, "waiting_for": next_field})
            await send_question(update, next_field, "✅ ذخیره شد!")
        else:
            # همه فیلدها پر شدند - نمایش خلاصه
            set_state(user_id, {"data": data, "waiting_for": "confirmation"})
            await send_summary(update, data)
        return
    
    # ========== حالت ۲: تایید نهایی ==========
    if state.get("waiting_for") == "confirmation":
        action = normalize_button_input(text, "confirmation")
        
        if action == "confirm":
            # نرمال‌سازی موقعیت
            location_str = f"{data.get('neighborhood', '')} {data.get('city', '')}"
            normalized = normalize_location(location_str)
            if normalized:
                data["neighborhood"] = normalized.get("neighborhood", data.get("neighborhood"))
                data["city"] = normalized.get("city", data.get("city"))
            
            # اعمال قوانین
            data = apply_rules(data)
            
            # ذخیره نهایی
            logger.info(f"✅ Property saved for user {user_id}: {data}")
            clear_state(user_id)
            
            await update.message.reply_text(
                "✅ ملک شما با موفقیت ثبت شد!\n\n"
                f"📋 خلاصه:\n{format_property_summary(data)}",
                reply_markup=ReplyKeyboardRemove()
            )
        
        elif action == "edit":
            set_state(user_id, {"data": data, "waiting_for": "transaction_type"})
            await send_question(update, "transaction_type", "✏️ ویرایش - از اول شروع کنید:")
        
        elif action == "cancel":
            clear_state(user_id)
            await update.message.reply_text("🗑️ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
        
        return
    
    # ========== حالت ۳: پیام جدید - استخراج اطلاعات ==========
    try:
        extracted = extract_property_info(text)
        if extracted:
            data.update(extracted)
            logger.info(f"Extracted data: {extracted}")
    except Exception as e:
        logger.error(f"Extraction error: {e}")
    
    # بررسی فیلدهای خالی
    missing = get_missing_fields(data)
    
    if missing:
        next_field = missing[0]
        set_state(user_id, {"data": data, "waiting_for": next_field})
        
        prefix = "📝 اطلاعات دریافت شد. لطفاً موارد زیر را تکمیل کنید:" if data else None
        await send_question(update, next_field, prefix)
    else:
        set_state(user_id, {"data": data, "waiting_for": "confirmation"})
        await send_summary(update, data)

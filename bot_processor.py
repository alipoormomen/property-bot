# bot_processor.py - Main Processing Logic with Reply Keyboard Support
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes

from conversation_state import ConversationState
from rule_engine import apply_rules
from extractor import extract_property_info
from bot_utils import (
    format_property_summary,
    format_confirmation_message,
    parse_field_from_text,
    normalize_yes_no,
    text_to_int
)
from services.inference_service import normalize_location

logger = logging.getLogger(__name__)

# ========================================
# 🎹 Reply Keyboard Options
# ========================================

KEYBOARD_OPTIONS = {
    "transaction_type": {
        "question": "نوع معامله را انتخاب کنید:",
        "buttons": [
            ["🏷️ فروش", "🔑 رهن و اجاره"],
            ["🏗️ پیش‌فروش"]
        ],
        "mapping": {
            "🏷️ فروش": "Sale",
            "فروش": "Sale",
            "🔑 رهن و اجاره": "Rent",
            "رهن و اجاره": "Rent",
            "رهن": "Rent",
            "اجاره": "Rent",
            "🏗️ پیش‌فروش": "Pre-sale",
            "پیش‌فروش": "Pre-sale",
            "پیش فروش": "Pre-sale"
        }
    },
    "property_type": {
        "question": "نوع ملک را انتخاب کنید:",
        "buttons": [
            ["🏢 آپارتمان", "🏠 ویلا"],
            ["🏬 مغازه", "🌍 زمین"]
        ],
        "mapping": {
            "🏢 آپارتمان": "Apartment",
            "آپارتمان": "Apartment",
            "🏠 ویلا": "Villa",
            "ویلا": "Villa",
            "🏬 مغازه": "Shop",
            "مغازه": "Shop",
            "🌍 زمین": "Land",
            "زمین": "Land"
        }
    },
    "usage_type": {
        "question": "نوع کاربری ملک را انتخاب کنید:",
        "buttons": [
            ["🏠 مسکونی", "🏪 تجاری"],
            ["🏛️ اداری"]
        ],
        "mapping": {
            "🏠 مسکونی": "Residential",
            "مسکونی": "Residential",
            "🏪 تجاری": "Commercial",
            "تجاری": "Commercial",
            "🏛️ اداری": "Administrative",
            "اداری": "Administrative"
        }
    },
    "has_elevator": {
        "question": "آیا ملک آسانسور دارد؟",
        "buttons": [
            ["✅ بله، دارد", "❌ خیر، ندارد"]
        ],
        "mapping": {
            "✅ بله، دارد": True,
            "بله": True,
            "دارد": True,
            "آره": True,
            "❌ خیر، ندارد": False,
            "خیر": False,
            "ندارد": False,
            "نه": False
        }
    },
    "has_parking": {
        "question": "آیا ملک پارکینگ دارد؟",
        "buttons": [
            ["✅ بله، دارد", "❌ خیر، ندارد"]
        ],
        "mapping": {
            "✅ بله، دارد": True,
            "بله": True,
            "دارد": True,
            "آره": True,
            "❌ خیر، ندارد": False,
            "خیر": False,
            "ندارد": False,
            "نه": False
        }
    },
    "has_storage": {
        "question": "آیا ملک انباری دارد؟",
        "buttons": [
            ["✅ بله، دارد", "❌ خیر، ندارد"]
        ],
        "mapping": {
            "✅ بله، دارد": True,
            "بله": True,
            "دارد": True,
            "آره": True,
            "❌ خیر، ندارد": False,
            "خیر": False,
            "ندارد": False,
            "نه": False
        }
    },
    "confirmation": {
        "question": "آیا اطلاعات بالا صحیح است؟",
        "buttons": [
            ["✅ تایید و ثبت", "✏️ ویرایش"],
            ["🗑️ لغو و شروع مجدد"]
        ],
        "mapping": {
            "✅ تایید و ثبت": "confirm",
            "تایید": "confirm",
            "بله": "confirm",
            "✏️ ویرایش": "edit",
            "ویرایش": "edit",
            "🗑️ لغو و شروع مجدد": "cancel",
            "لغو": "cancel",
            "انصراف": "cancel"
        }
    }
}


# ========================================
# 🔧 Helper Functions
# ========================================

def normalize_button_input(text: str, field: str) -> any:
    """
    تبدیل متن دکمه به مقدار سیستمی
    مثال: "🏷️ فروش" -> "Sale"
    """
    if field in KEYBOARD_OPTIONS:
        mapping = KEYBOARD_OPTIONS[field].get("mapping", {})
        # اول دقیق چک کن
        if text in mapping:
            return mapping[text]
        # بعد بدون ایموجی چک کن
        text_clean = text.strip()
        for key, value in mapping.items():
            if key.endswith(text_clean) or text_clean.endswith(key.replace("🏷️ ", "").replace("🔑 ", "").replace("🏗️ ", "").replace("🏢 ", "").replace("🏠 ", "").replace("🏬 ", "").replace("🌍 ", "").replace("✅ ", "").replace("❌ ", "").replace("✏️ ", "").replace("🗑️ ", "")):
                return value
    return text


def get_reply_keyboard(field: str) -> ReplyKeyboardMarkup:
    """
    ساخت Reply Keyboard برای فیلد مشخص
    """
    if field not in KEYBOARD_OPTIONS:
        return None
    
    buttons = KEYBOARD_OPTIONS[field]["buttons"]
    keyboard = [[KeyboardButton(btn) for btn in row] for row in buttons]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_question_for_field(field: str) -> str:
    """
    دریافت سوال مناسب برای فیلد
    """
    if field in KEYBOARD_OPTIONS:
        return KEYBOARD_OPTIONS[field]["question"]
    
    # سوالات پیش‌فرض برای فیلدهای بدون دکمه
    default_questions = {
        "neighborhood": "📍 محله ملک را وارد کنید:",
        "city": "🏙️ شهر ملک را وارد کنید:",
        "area": "📐 متراژ ملک را وارد کنید (به متر مربع):",
        "bedroom_count": "🛏️ تعداد اتاق خواب را وارد کنید:",
        "floor": "🏢 طبقه واحد را وارد کنید:",
        "total_floors": "🏗️ تعداد کل طبقات ساختمان را وارد کنید:",
        "unit_count": "🚪 تعداد واحد در هر طبقه را وارد کنید:",
        "build_year": "📅 سال ساخت را وارد کنید:",
        "price_total": "💰 قیمت کل یا مبلغ رهن را وارد کنید (تومان):",
        "rent": "💵 مبلغ اجاره ماهانه را وارد کنید (تومان):",
        "owner_name": "👤 نام مالک را وارد کنید:",
        "owner_phone": "📞 شماره تماس مالک را وارد کنید:"
    }
    
    return default_questions.get(field, f"لطفاً {field} را وارد کنید:")


def has_keyboard(field: str) -> bool:
    """
    آیا این فیلد دکمه دارد؟
    """
    return field in KEYBOARD_OPTIONS and field != "confirmation"


# ========================================
# 🚀 Main Processing Functions
# ========================================

async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    پردازش اصلی ورودی کاربر
    """
    user_id = update.effective_user.id
    state = ConversationState.get_or_create(user_id)
    
    logger.info(f"[User {user_id}] Input: {text[:50]}... | State: {state.current_step}")
    
    # --- بررسی دستورات خاص ---
    if text in ["لغو", "انصراف", "/cancel"]:
        state.reset()
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n\nبرای شروع مجدد، اطلاعات ملک را ارسال کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    if text in ["/start", "شروع"]:
        state.reset()
        await update.message.reply_text(
            "سلام! 👋\n\n"
            "من ربات ثبت ملک هستم.\n"
            "اطلاعات ملک را به هر شکلی که راحتید بفرستید.\n\n"
            "مثال:\n"
            "«آپارتمان ۱۲۰ متری در گلسار برای فروش»\n\n"
            "یا می‌توانید ویس بفرستید 🎤",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # --- اگر در مرحله تایید نهایی هستیم ---
    if state.current_step == "confirmation":
        await handle_confirmation_response(update, context, state, text)
        return
    
    # --- اگر منتظر پاسخ به سوال خاصی هستیم ---
    if state.waiting_for_field:
        await handle_field_response(update, context, state, text)
        return
    
    # --- استخراج اطلاعات از متن آزاد ---
    await process_free_text(update, context, state, text)


async def process_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, text: str):
    """
    پردازش متن آزاد و استخراج اطلاعات
    """
    user_id = update.effective_user.id
    
    try:
        # استخراج اطلاعات با AI
        extracted = await extract_property_info(text)
        logger.info(f"[User {user_id}] Extracted: {extracted}")
        
        if not extracted or extracted.get("error"):
            await update.message.reply_text(
                "⚠️ متوجه نشدم. لطفاً واضح‌تر بنویسید.\n\n"
                "مثال: آپارتمان ۱۲۰ متری در گلسار برای فروش"
            )
            return
        
        # ادغام اطلاعات جدید با قبلی
        for key, value in extracted.items():
            if value is not None and value != "":
                state.data[key] = value
        
        # نرمال‌سازی موقعیت
        if extracted.get("neighborhood") or extracted.get("city"):
            location_text = f"{extracted.get('neighborhood', '')} {extracted.get('city', '')}".strip()
            if location_text:
                try:
                    loc = normalize_location(location_text)
                    if loc.get("city"):
                        state.data["city"] = loc["city"]
                    if loc.get("neighborhood"):
                        state.data["neighborhood"] = loc["neighborhood"]
                except Exception as e:
                    logger.warning(f"Location normalization failed: {e}")
        
        # اعمال قوانین و تعیین مرحله بعدی
        result = apply_rules(state.data)
        await send_response_with_keyboard(update, context, state, result)
        
    except Exception as e:
        logger.error(f"[User {user_id}] Error in process_free_text: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )


async def handle_field_response(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, text: str):
    """
    پردازش پاسخ به سوال خاص (مثلاً وقتی منتظر نوع معامله هستیم)
    """
    user_id = update.effective_user.id
    field = state.waiting_for_field
    
    logger.info(f"[User {user_id}] Field response for '{field}': {text}")
    
    # تبدیل متن دکمه به مقدار سیستمی
    value = normalize_button_input(text, field)
    
    # اعتبارسنجی مقدار
    if field in ["area", "bedroom_count", "floor", "total_floors", "unit_count", "build_year"]:
        int_value = text_to_int(text)
        if int_value is None:
            await update.message.reply_text(
                "⚠️ لطفاً یک عدد معتبر وارد کنید.",
                reply_markup=get_reply_keyboard(field) if has_keyboard(field) else ReplyKeyboardRemove()
            )
            return
        state.data[field] = int_value
    elif field in ["price_total", "rent"]:
        int_value = text_to_int(text)
        if int_value is None:
            await update.message.reply_text(
                "⚠️ لطفاً مبلغ را به‌صورت عددی وارد کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        state.data[field] = int_value
    elif field in ["has_elevator", "has_parking", "has_storage"]:
        bool_value = normalize_yes_no(text)
        if bool_value is None:
            await update.message.reply_text(
                "⚠️ لطفاً یکی از گزینه‌ها را انتخاب کنید.",
                reply_markup=get_reply_keyboard(field)
            )
            return
        state.data[field] = bool_value
    else:
        state.data[field] = value

    # پاک کردن وضعیت انتظار
    state.waiting_for_field = None

    # اعمال قوانین برای مرحله بعد
    result = apply_rules(state.data)
    await send_response_with_keyboard(update, context, state, result)


async def handle_confirmation_response(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       state: ConversationState, text: str):
    """
    پاسخ کاربر در مرحله تایید نهایی
    """
    action = normalize_button_input(text, "confirmation")

    if action == "confirm":
        summary = format_property_summary(state.data)
        await update.message.reply_text(
            "✅ ملک با موفقیت ثبت شد.\n\n" + summary,
            reply_markup=ReplyKeyboardRemove()
        )
        state.reset()
        return

    if action == "edit":
        await update.message.reply_text(
            "✏️ لطفاً فیلدی که می‌خواهید ویرایش کنید ارسال کنید.\n"
            "مثال:\n"
            "متراژ: 130",
            reply_markup=ReplyKeyboardRemove()
        )
        state.current_step = "editing"
        return

    if action == "cancel":
        state.reset()
        await update.message.reply_text(
            "❌ عملیات لغو شد.\nبرای شروع مجدد، اطلاعات ملک را ارسال کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    await update.message.reply_text(
        "⚠️ لطفاً یکی از گزینه‌ها را انتخاب کنید.",
        reply_markup=get_reply_keyboard("confirmation")
    )


async def send_response_with_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      state: ConversationState, result: dict):
    """
    ارسال پیام همراه با Reply Keyboard در صورت نیاز
    """
    if result.get("status") == "ask":
        field = result.get("missing")
        question = get_question_for_field(field)

        state.waiting_for_field = field
        state.current_step = field

        keyboard = get_reply_keyboard(field) if has_keyboard(field) else ReplyKeyboardRemove()

        await update.message.reply_text(
            question,
            reply_markup=keyboard
        )
        return

    if result.get("status") == "confirm":
        msg = format_confirmation_message(state.data)
        state.current_step = "confirmation"

        await update.message.reply_text(
            msg,
            reply_markup=get_reply_keyboard("confirmation")
        )
        return

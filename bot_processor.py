# bot_processor.py - FINAL COMPLETE VERSION
import logging
from typing import Dict, Optional
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove

from extractor import extract_json
from phone_utils import normalize_iran_phone
from rule_engine import run_rule_engine
from conversation_state import (
    merge_state,
    get_pending_field,
    get_state,
    clear_state,
    set_confirmation_mode,
    is_confirmation_mode,
    set_pending_field,
)
from services.inference_service import (
    infer_property_type,
    infer_usage_type,
    normalize_location,
)
from utils import normalize_price, validate_area, validate_floor
from bot_utils import (
    text_to_int,
    normalize_yes_no,
    format_confirmation_message,
    parse_field_from_text,
)

logger = logging.getLogger(__name__)

# ============================================
# ✅ دکمه‌های انتخاب برای فیلدهای خاص
# ============================================
KEYBOARD_OPTIONS = {
    "transaction_type": [["🏷 فروش", "🔑 رهن و اجاره"], ["🏗 پیش‌فروش"]],
    "property_type": [["🏢 آپارتمان", "🏡 ویلا"], ["🌍 زمین", "🏪 مغازه"]],
    "usage_type": [["🏠 مسکونی", "🏬 تجاری"], ["🏛 اداری"]],
    "has_parking": [["✅ بله", "❌ خیر"]],
    "has_elevator": [["✅ بله", "❌ خیر"]],
    "has_storage": [["✅ بله", "❌ خیر"]],
}

# ============================================
# ✅ مپ تبدیل متن دکمه به مقدار واقعی
# ============================================
BUTTON_VALUE_MAP = {
    "🏷 فروش": "فروش",
    "🔑 رهن و اجاره": "رهن و اجاره",
    "🏗 پیش‌فروش": "پیش‌فروش",
    "🏢 آپارتمان": "آپارتمان",
    "🏡 ویلا": "ویلا",
    "🌍 زمین": "زمین",
    "🏪 مغازه": "مغازه",
    "🏠 مسکونی": "مسکونی",
    "🏬 تجاری": "تجاری",
    "🏛 اداری": "اداری",
    "✅ بله": True,
    "❌ خیر": False,
}


def get_reply_keyboard(field_name: str) -> Optional[ReplyKeyboardMarkup]:
    """ساخت ReplyKeyboard برای فیلدهای انتخابی"""
    if field_name in KEYBOARD_OPTIONS:
        return ReplyKeyboardMarkup(
            KEYBOARD_OPTIONS[field_name],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    return None


def normalize_button_input(text: str):
    """تبدیل متن دکمه (با ایموجی) به مقدار واقعی"""
    return BUTTON_VALUE_MAP.get(text.strip(), text.strip())


async def handle_edit_request(user_id: int, text: str, update: Update) -> bool:
    """Handle field edit requests in confirmation mode"""
    parsed = parse_field_from_text(text)
    if not parsed:
        return False

    field_name, new_value = parsed
    logger.info(f"Edit request: {field_name} = {new_value}")

    current_state = get_state(user_id)
    processed_value = new_value

    if field_name in ["area", "bedroom_count", "floor", "parking_count", "storage_count", "total_floors", "unit_count", "build_year"]:
        processed_value = text_to_int(new_value)
    elif field_name in ["price_total", "rent", "deposit"]:
        processed_value = normalize_price(new_value)
    elif field_name.startswith("has_"):
        processed_value = normalize_yes_no(new_value)
    elif field_name == "owner_phone":
        processed_value = normalize_iran_phone(new_value)

    current_state[field_name] = processed_value
    merge_state(user_id, {field_name: processed_value})

    await update.message.reply_text(
        f"✅ فیلد '{field_name}' به '{processed_value}' تغییر یافت.\n\n"
        f"{format_confirmation_message(current_state)}",
        reply_markup=ReplyKeyboardRemove()
    )
    return True


async def process_text(text: str, user_id: int, update: Update):
    """Main text processing function"""
    logger.info(f"INPUT from user {user_id}: {text}")

    normalized_text = normalize_button_input(text)
    clean_text = str(normalized_text).strip().replace('"', "")

    # Handle confirmation mode
    if is_confirmation_mode(user_id):
        current_state = get_state(user_id)

        if clean_text.lower() in ["تأیید", "بله", "اره", "آره", "ok", "yes", "تایید"] or normalized_text is True:
            await update.message.reply_text(
                "✅ اطلاعات ملک با موفقیت ثبت شد!\n"
                "🙏 از همکاری شما متشکریم.\n\n"
                "برای ثبت ملک جدید، اطلاعات را ارسال کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
            clear_state(user_id)
            return

        edit_handled = await handle_edit_request(user_id, text, update)
        if edit_handled:
            return

        await update.message.reply_text(
            "لطفا یکی از موارد زیر را انتخاب کنید:\n"
            "- برای تایید: 'بله' یا 'تایید'\n"
            "- برای ویرایش: 'محله: گلسار' (فرمت: نام_فیلد: مقدار)"
        )
        return

    # Extract with LLM
    extracted = extract_json(text)
    pending_field = get_pending_field(user_id)
    val_int = text_to_int(clean_text)

    # اگر ورودی از دکمه بود
    if normalized_text != text.strip() and pending_field:
        extracted[pending_field] = normalized_text
        logger.info(f"Button Input: Set {pending_field} to {normalized_text}")

    # Context-Aware Processing
    elif pending_field:
        if pending_field == "transaction_type":
            normalized = clean_text.lower().strip()
            if normalized in ["اجاره", "رهن", "اجارە"]:
                extracted[pending_field] = "رهن و اجاره"
            elif normalized in ["فروش", "خرید"]:
                extracted[pending_field] = "فروش"
            elif normalized in ["پیش فروش", "پیشفروش", "پیش‌فروش"]:
                extracted[pending_field] = "پیش‌فروش"

        elif pending_field == "property_type":
            normalized = clean_text.lower().strip()
            if normalized in ["آپارتمان", "اپارتمان"]:
                extracted[pending_field] = "آپارتمان"
            elif normalized in ["ویلا", "ویلایی"]:
                extracted[pending_field] = "ویلا"
            elif normalized in ["زمین"]:
                extracted[pending_field] = "زمین"
            elif normalized in ["مغازه", "غازه"]:
                extracted[pending_field] = "مغازه"

        elif pending_field == "usage_type":
            normalized = clean_text.lower().strip()
            if normalized in ["مسکونی"]:
                extracted[pending_field] = "مسکونی"
            elif normalized in ["تجاری"]:
                extracted[pending_field] = "تجاری"
            elif normalized in ["اداری"]:
                extracted[pending_field] = "اداری"

        elif pending_field in ["bedroom_count", "floor", "parking_count", "storage_count", "unit_count", "area", "total_floors", "build_year"]:
            if val_int is not None:
                extracted[pending_field] = val_int

        elif pending_field in ["price_total", "rent", "deposit", "price"]:
            price_val = normalize_price(clean_text)
            if price_val:
                extracted[pending_field] = price_val
            elif val_int is not None:
                extracted[pending_field] = val_int

        elif pending_field.startswith("has_"):
            bool_val = normalize_yes_no(clean_text)
            if bool_val is not None:
                extracted[pending_field] = bool_val

        elif pending_field in ["owner_name", "neighborhood"]:
            if val_int is None and 2 < len(clean_text) < 30:
                extracted[pending_field] = clean_text

        elif pending_field == "owner_phone":
            phone = normalize_iran_phone(clean_text)
            if phone:
                extracted[pending_field] = phone

        elif pending_field == "address":
            if len(clean_text) > 5:
                extracted[pending_field] = clean_text

    # Inference
    current_state = get_state(user_id)

    if "property_type" not in extracted and "property_type" not in current_state:
        inferred_property = infer_property_type(text)
        if inferred_property:
            extracted["property_type"] = inferred_property

    if "usage_type" not in extracted and "usage_type" not in current_state:
        inferred_usage = infer_usage_type(text)
        if inferred_usage:
            extracted["usage_type"] = inferred_usage

    # Normalize phone
    if "owner_phone" in extracted:
        extracted["owner_phone"] = normalize_iran_phone(extracted["owner_phone"])
    # Normalize phone
    if "owner_phone" in extracted:
        extracted["owner_phone"] = normalize_iran_phone(extracted["owner_phone"])

    # Normalize prices
    for price_field in ["price_total", "rent", "deposit"]:
        if price_field in extracted and isinstance(extracted[price_field], str):
            extracted[price_field] = normalize_price(extracted[price_field])

    # Normalize location - ✅ اصلاح شده
    if "neighborhood" in extracted or "city" in extracted or "address" in extracted:
        loc = normalize_location(extracted)
        if loc.get("neighborhood"):
            extracted["neighborhood"] = loc["neighborhood"]
        if loc.get("city"):
            extracted["city"] = loc["city"]

    # Merge state
    if extracted:
        merge_state(user_id, extracted)
        logger.info(f"Merged state for user {user_id}: {extracted}")
   

    # Run Rule Engine
    current_state = get_state(user_id)
    current_state["_user_id"] = user_id
    result = run_rule_engine(current_state)

    logger.info(f"Rule Engine Result: {result}")

    # Send response
    await send_response_with_keyboard(result, update, user_id)


async def send_response_with_keyboard(result: Dict, update: Update, user_id: int):
    """ارسال پاسخ Rule Engine با دکمه‌های مناسب"""
    if result.get("status") == "ask":
        question = result.get("question", "لطفاً اطلاعات بیشتری وارد کنید.")
        missing_field = result.get("missing")

        if missing_field:
            set_pending_field(user_id, missing_field)

        keyboard = get_reply_keyboard(missing_field)
        if keyboard:
            await update.message.reply_text(question, reply_markup=keyboard)
        else:
            await update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())

    elif result.get("status") == "completed":
        set_confirmation_mode(user_id, True)

        state = get_state(user_id)
        confirmation_text = format_confirmation_message(state)

        keyboard = ReplyKeyboardMarkup(
            [["✅ تایید", "✏️ ویرایش"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(confirmation_text, reply_markup=keyboard)

    else:
        await update.message.reply_text(
            "لطفاً اطلاعات بیشتری ارسال کنید.",
            reply_markup=ReplyKeyboardRemove()
        )


async def handle_callback_query(update, context):
    """پردازش کلیک روی دکمه‌های Inline Keyboard"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user_id = query.from_user.id

    if callback_data.startswith("field:"):
        parts = callback_data.split(":", 2)
        if len(parts) == 3:
            _, field_name, value = parts
            response = await process_button_selection(user_id, field_name, value, context)
            await query.edit_message_text(text=response)
        else:
            await query.edit_message_text(text="❌ خطا در پردازش انتخاب")
    elif callback_data == "confirm:yes":
        await query.edit_message_text(text="✅ اطلاعات شما با موفقیت ثبت شد!")
    elif callback_data == "confirm:no":
        await query.edit_message_text(text="🔄 لطفاً اطلاعات را مجدداً وارد کنید.")
    else:
        await query.edit_message_text(text="❓ دستور نامشخص")


async def process_button_selection(user_id, field_name, value, context):
    """پردازش انتخاب دکمه و به‌روزرسانی state"""
    return f"✅ مقدار «{value}» برای فیلد «{field_name}» ثبت شد."

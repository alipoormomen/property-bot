# bot_processor.py - UPDATED with Keyboard Buttons
import logging
from typing import Dict
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

# ✅ دکمه‌های انتخاب برای فیلدهای خاص
KEYBOARD_OPTIONS = {
    "transaction_type": [["فروش", "رهن و اجاره"], ["پیش‌فروش"]],
    "property_type": [["آپارتمان", "ویلا"], ["زمین", "مغازه"]],
    "usage_type": [["مسکونی", "تجاری"], ["اداری"]],
    "has_parking": [["بله", "خیر"]],
    "has_elevator": [["بله", "خیر"]],
    "has_storage": [["بله", "خیر"]],
}

async def handle_edit_request(user_id: int, text: str, update: Update) -> bool:
    """Handle field edit requests in confirmation mode"""
    parsed = parse_field_from_text(text)
    if not parsed:
        return False

    field_name, new_value = parsed
    logger.info(f"Edit request: {field_name} = {new_value}")

    current_state = get_state(user_id)
    processed_value = new_value

    # Process based on field type
    if field_name in ["area", "bedroom_count", "floor", "parking_count", "storage_count", "total_floors", "unit_count", "build_year"]:
        processed_value = text_to_int(new_value)
    elif field_name in ["price_total", "rent", "deposit"]:
        processed_value = normalize_price(new_value)
    elif field_name.startswith("has_"):
        processed_value = normalize_yes_no(new_value)
    elif field_name == "owner_phone":
        processed_value = normalize_iran_phone(new_value)

    # Update state
    current_state[field_name] = processed_value
    merge_state(user_id, {field_name: processed_value})

    await update.message.reply_text(
        f"فیلد '{field_name}' به '{processed_value}' تغییر یافت.\n\n"
        f"{format_confirmation_message(current_state)}"
    )
    return True

async def process_text(text: str, user_id: int, update: Update):
    """Main text processing function"""
    logger.info(f"INPUT from user {user_id}: {text}")

    # Handle confirmation mode
    if is_confirmation_mode(user_id):
        current_state = get_state(user_id)

        # Check for confirmation
        if text.strip().lower() in ["تأیید", "بله", "اره", "آره", "ok", "yes", "تایید"]:
            await update.message.reply_text(
                "✅ اطلاعات ملک با موفقیت ثبت شد!\nاز همکاری شما متشکریم.",
                reply_markup=ReplyKeyboardRemove()
            )
            clear_state(user_id)
            return

        # Check for edit request
        edit_handled = await handle_edit_request(user_id, text, update)
        if edit_handled:
            return

        # Invalid input in confirmation mode
        await update.message.reply_text(
            "لطفا یکی از موارد زیر را انتخاب کنید:\n"
            "- برای تایید: 'بله' یا 'تایید'\n"
            "- برای ویرایش: 'محله: گلسار' (فرمت: نام_فیلد: مقدار)"
        )
        return

    # Extract with LLM
    extracted = extract_json(text)
    clean_text = text.strip().replace('"', "")
    pending_field = get_pending_field(user_id)
    val_int = text_to_int(clean_text)

    # Context-Aware Processing
    if pending_field:
        # ✅ برای فیلدهای متنی خاص، نرمال‌سازی انجام بده
        if pending_field == "transaction_type":
            normalized = clean_text.lower().strip()
            if normalized in ["اجاره", "رهن", "اجارە"]:
                extracted[pending_field] = "رهن و اجاره"
                logger.info(f"Context Fill: Set {pending_field} to رهن و اجاره")
            elif normalized in ["فروش", "خرید"]:
                extracted[pending_field] = "فروش"
                logger.info(f"Context Fill: Set {pending_field} to فروش")
            elif normalized in ["پیش فروش", "پیشفروش", "پیش‌فروش"]:
                extracted[pending_field] = "پیش‌فروش"
                logger.info(f"Context Fill: Set {pending_field} to پیش‌فروش")

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

        elif pending_field in ["bedroom_count", "floor", "parking_count", "storage_count", "unit_count", "area", "total_floors", "build_year"]:
            if val_int is not None:
                extracted[pending_field] = val_int
                logger.info(f"Context Fill: Set {pending_field} to {val_int}")

        elif pending_field in ["price_total", "rent", "deposit", "price"]:
            if val_int is not None:
                extracted[pending_field] = val_int
                logger.info(f"Context Fill: Set {pending_field} to {val_int}")

        elif pending_field.startswith("has_"):
            bool_val = normalize_yes_no(clean_text)
            if bool_val is not None:
                extracted[pending_field] = bool_val
                logger.info(f"Context Fill: Set {pending_field} to {bool_val}")

        elif pending_field in ["owner_name", "neighborhood", "usage_type"]:
            if val_int is None and 2 < len(clean_text) < 30:
                extracted[pending_field] = clean_text
                logger.info(f"Context Fill: Set {pending_field} to {clean_text}")

        elif pending_field == "owner_phone":
            normalized_phone = normalize_iran_phone(clean_text)
            if normalized_phone:
                extracted["owner_phone"] = normalized_phone
                logger.info(f"Context Fill: Set owner_phone to {normalized_phone}")

    # Normalize phone
    if extracted.get("owner_phone"):
        extracted["owner_phone"] = normalize_iran_phone(extracted["owner_phone"])

    # Normalize prices
    for price_k in ["price_total", "rent", "deposit"]:
        if extracted.get(price_k):
            extracted[price_k] = normalize_price(extracted[price_k])

    # Validate area and floor
    if extracted.get("area"):
        validated_area = validate_area(extracted["area"])
        extracted["area"] = validated_area if validated_area else extracted["area"]

    if extracted.get("floor"):
        validated_floor = validate_floor(extracted["floor"])
        extracted["floor"] = validated_floor if validated_floor else extracted["floor"]

    # Get current state
    current_state = get_state(user_id)

    # Prevent property_type override
    if current_state.get("property_type") and extracted.get("property_type"):
        logger.info(f"Ignoring new property_type, keeping: {current_state['property_type']}")
        del extracted["property_type"]

    # Inference Layer
    if not extracted.get("property_type"):
        extracted = infer_property_type(extracted)
    if not extracted.get("usage_type"):
        extracted = infer_usage_type(extracted)
    extracted = normalize_location(extracted)

    # Merge state
    data = merge_state(user_id, extracted)
    data["_user_id"] = user_id

    # Rule engine
    result = run_rule_engine(data)

    if result["status"] == "completed":
        set_confirmation_mode(user_id, True)
        confirmation_msg = format_confirmation_message(data)
        keyboard = [["تایید", "ویرایش"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(confirmation_msg, reply_markup=reply_markup)

    elif result.get("question"):
        # ✅ اگر فیلد جاری دکمه داشت، نمایش بده
        pending = result.get("pending_field")
        if pending and pending in KEYBOARD_OPTIONS:
            keyboard = KEYBOARD_OPTIONS[pending]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(result["question"], reply_markup=reply_markup)
        else:
            await update.message.reply_text(result["question"], reply_markup=ReplyKeyboardRemove())

    else:
        await update.message.reply_text("لطفا اطلاعات بیشتری ارسال کنید.", reply_markup=ReplyKeyboardRemove())

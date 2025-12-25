# bot_processor_core/processor.py
"""منطق اصلی پردازش متن"""

import logging
import re
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
from services.inference_service import infer_property_type, infer_usage_type, normalize_location
from utils import normalize_price
from bot_utils import text_to_int, normalize_yes_no, format_confirmation_message

from .constants import (
    KEYBOARD_OPTIONS,
    NUMERIC_FIELDS,
    PRICE_FIELDS,
    TEXT_FIELDS,
    FREE_TEXT_FIELDS,
)
from .utils import (
    normalize_button_input,
    is_button_input,
    get_reply_keyboard,
    normalize_transaction_type,
    normalize_property_type,
    normalize_usage_type,
)
from .handlers import handle_edit_request

logger = logging.getLogger(__name__)


async def process_text(text: str, user_id: int, update: Update):
    """Main text processing function"""
    logger.info(f"INPUT from user {user_id}: {text}")

    normalized_text = normalize_button_input(text)
    clean_text = str(normalized_text).strip().replace('"', "")

    # حالت تایید
    if is_confirmation_mode(user_id):
        await _handle_confirmation_mode(user_id, clean_text, normalized_text, text, update)
        return

    # استخراج با LLM
    extracted = extract_json(text)
    if extracted is None:
        extracted = {}

    pending_field = get_pending_field(user_id)
    val_int = text_to_int(clean_text)

    # پردازش ورودی
    if is_button_input(text, normalized_text) and pending_field:
        extracted[pending_field] = normalized_text
        set_pending_field(user_id, None)
        logger.info(f"Button Input: Set {pending_field} to {normalized_text}")
    elif pending_field:
        extracted = _process_pending_field(
            pending_field, clean_text, val_int, extracted, text, user_id
        )

    # Inference
    current_state = get_state(user_id)
    extracted = _apply_inference(text, extracted, current_state)

    # نرمال‌سازی
    extracted = _normalize_extracted_data(extracted)

    # ذخیره و Rule Engine
    if extracted:
        merge_state(user_id, extracted)
        logger.info(f"Merged state for user {user_id}: {extracted}")

    current_state = get_state(user_id)
    current_state["_user_id"] = user_id
    result = run_rule_engine(current_state)

    logger.info(f"Rule Engine Result: {result}")

    await _send_response_with_keyboard(result, update, user_id)


async def _handle_confirmation_mode(
    user_id: int, clean_text: str, normalized_text, original_text: str, update: Update
):
    """پردازش حالت تایید نهایی"""
    current_state = get_state(user_id)

    # تایید نهایی
    if clean_text.lower() in ["تأیید", "بله", "اره", "آره", "ok", "yes", "تایید"] or normalized_text == "تایید":
        await update.message.reply_text(
            "✅ اطلاعات ملک با موفقیت ثبت شد!\n"
            "🙏 از همکاری شما متشکریم.\n\n"
            "برای ثبت ملک جدید، اطلاعات را ارسال کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        clear_state(user_id)
        return

    # ویرایش
    if clean_text == "ویرایش":
        set_confirmation_mode(user_id, False)
        await update.message.reply_text(
            "✏️ فیلد مورد نظر را به این فرمت ارسال کنید:\n"
            "مثال: متراژ: 120\n"
            "یا: قیمت = 5 میلیارد",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # بررسی درخواست ویرایش مستقیم
    edit_handled = await handle_edit_request(user_id, original_text, update)
    if edit_handled:
        return

    # پیام راهنما
    keyboard = ReplyKeyboardMarkup(
        KEYBOARD_OPTIONS["confirmation"],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=keyboard
    )


def _process_pending_field(
    pending_field: str,
    clean_text: str,
    val_int: Optional[int],
    extracted: Dict,
    original_text: str,
    user_id: int
) -> Dict:
    """پردازش مقدار فیلد در انتظار"""

    # ✅ فیلدهای متنی آزاد - مهم‌ترین اصلاح
    if pending_field in FREE_TEXT_FIELDS:
        extracted[pending_field] = clean_text
        set_pending_field(user_id, None)
        logger.info(f"Free text field set: {pending_field} = {clean_text}")
        return extracted

    # نوع معامله
    if pending_field == "transaction_type":
        value = normalize_transaction_type(clean_text)
        extracted[pending_field] = value if value else clean_text
        set_pending_field(user_id, None)

    # نوع ملک
    elif pending_field == "property_type":
        value = normalize_property_type(clean_text)
        extracted[pending_field] = value if value else clean_text
        set_pending_field(user_id, None)

    # نوع کاربری
    elif pending_field == "usage_type":
        value = normalize_usage_type(clean_text)
        extracted[pending_field] = value if value else clean_text
        set_pending_field(user_id, None)

    # فیلدهای عددی
    elif pending_field in NUMERIC_FIELDS:
        if val_int is not None:
            extracted[pending_field] = val_int
        else:
            numbers = re.findall(r'\d+', clean_text)
            if numbers:
                extracted[pending_field] = int(numbers[0])
            else:
                extracted[pending_field] = clean_text
        set_pending_field(user_id, None)

    # فیلدهای قیمت
    elif pending_field in PRICE_FIELDS:
        normalized = normalize_price(clean_text)
        extracted[pending_field] = normalized if normalized else clean_text
        set_pending_field(user_id, None)

    # فیلدهای بله/خیر
    elif pending_field.startswith("has_"):
        yes_no = normalize_yes_no(clean_text)
        if yes_no is not None:
            extracted[pending_field] = yes_no
        else:
            extracted[pending_field] = clean_text.lower() in [
                "بله", "دارد", "داره", "اره", "آره", "yes", "true"
            ]
        set_pending_field(user_id, None)

    # شماره تلفن
    elif pending_field == "owner_phone":
        phone = normalize_iran_phone(clean_text)
        extracted[pending_field] = phone if phone else clean_text
        set_pending_field(user_id, None)

    # فیلدهای متنی عمومی
    elif pending_field in TEXT_FIELDS:
        extracted[pending_field] = clean_text
        set_pending_field(user_id, None)

    # سایر فیلدها
    else:
        extracted[pending_field] = clean_text
        set_pending_field(user_id, None)
        logger.info(f"Generic field set: {pending_field} = {clean_text}")

    return extracted


def _apply_inference(text: str, extracted: Dict, current_state: Dict) -> Dict:
    """اعمال استنتاج هوشمند"""

    # استنتاج نوع ملک
    if not extracted.get("property_type") and not current_state.get("property_type"):
        inferred = infer_property_type({"raw_text": text})
        if inferred and inferred.get("property_type"):
            extracted["property_type"] = inferred["property_type"]

    # استنتاج نوع کاربری
    if not extracted.get("usage_type") and not current_state.get("usage_type"):
        inferred = infer_usage_type({"raw_text": text})
        if inferred and inferred.get("usage_type"):
            extracted["usage_type"] = inferred["usage_type"]

    # نرمال‌سازی موقعیت
    location_data = {**current_state, **extracted}
    normalized_location = normalize_location(location_data)
    if normalized_location.get("neighborhood"):
        extracted["neighborhood"] = normalized_location["neighborhood"]
    if normalized_location.get("city"):
        extracted["city"] = normalized_location["city"]

    return extracted


def _normalize_extracted_data(extracted: Dict) -> Dict:
    """نرمال‌سازی نهایی داده‌ها"""

    # نرمال‌سازی قیمت‌ها
    for field in PRICE_FIELDS:
        if field in extracted and extracted[field]:
            if isinstance(extracted[field], str):
                normalized = normalize_price(extracted[field])
                if normalized:
                    extracted[field] = normalized

    # نرمال‌سازی شماره تلفن
    if "owner_phone" in extracted and extracted["owner_phone"]:
        phone = normalize_iran_phone(str(extracted["owner_phone"]))
        if phone:
            extracted["owner_phone"] = phone

    # حذف مقادیر خالی
    extracted = {k: v for k, v in extracted.items() if v is not None and v != ""}

    return extracted


async def _send_response_with_keyboard(result: Dict, update: Update, user_id: int):
    """ارسال پاسخ همراه با کیبورد مناسب"""

    message = result.get("message", "")
    next_field = result.get("next_field")
    complete = result.get("complete", False)

    # حالت تکمیل - نمایش خلاصه و تایید
    if complete:
        current_state = get_state(user_id)
        confirmation_msg = format_confirmation_message(current_state)
        keyboard = ReplyKeyboardMarkup(
            KEYBOARD_OPTIONS["confirmation"],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await update.message.reply_text(
            f"📋 خلاصه اطلاعات ملک:\n\n{confirmation_msg}\n\n"
            "آیا اطلاعات صحیح است؟",
            reply_markup=keyboard
        )
        set_confirmation_mode(user_id, True)
        return

    # سوال بعدی با کیبورد مناسب
    if next_field:
        set_pending_field(user_id, next_field)
        keyboard = get_reply_keyboard(next_field)

        if keyboard:
            await update.message.reply_text(message, reply_markup=keyboard)
        else:
            await update.message.reply_text(
                message,
                reply_markup=ReplyKeyboardRemove()
            )
        return

    # پیام ساده بدون کیبورد
    if message:
        await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

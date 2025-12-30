# bot_processor_core/processor.py
"""پردازشگر اصلی متن با اعتبارسنجی ورودی"""

import logging
from typing import Dict, Optional, Tuple
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove

from nocodb_client import (
    create_property,
    consume_credit,
    add_credit,
    is_confirmation_token_used,
)

from extractor import extract_json
from phone_utils import normalize_iran_phone
from rule_engine import run_rule_engine

from conversation_state import (
    merge_state,
    get_pending_field,
    set_pending_field,
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
from bot_utils import text_to_int, normalize_yes_no, format_confirmation_message

from .constants import (
    KEYBOARD_OPTIONS,
    FIELD_QUESTIONS,
    PRICE_FIELDS,
    FREE_TEXT_FIELDS,
    NUMERIC_FIELDS,
    BOOLEAN_FIELDS,
)

from .utils import (
    normalize_button_input,
    normalize_transaction_type,
    normalize_property_type,
    normalize_usage_type,
    normalize_boolean_field,
    get_reply_keyboard,
)

logger = logging.getLogger(__name__)

def persian_text_to_number(text: str) -> Optional[float]:
    """
    تبدیل متن فارسی قیمت به عدد
    مثال: "چهار میلیارد و دویست میلیون تومان" -> 4,200,000,000
    """
    if not text:
        return None

    original_text = text
    text = text.strip().lower()

    # اعداد فارسی به انگلیسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    for p, e in zip(persian_digits, english_digits):
        text = text.replace(p, e)

    # حذف "تومان" و "ریال" و کاراکترهای اضافی
    text = text.replace('تومان', '').replace('ریال', '').replace('تومن', '')
    text = text.replace('،', '').replace(',', '').strip()

    # اگر عدد مستقیم باشد
    clean = text.replace(' ', '')
    try:
        return float(clean)
    except ValueError:
        pass

    # === نرمال‌سازی کلمات ===
    # اصلاح غلط‌های املایی رایج
    text = text.replace('میلیادو', 'میلیارد و')
    text = text.replace('میلیادی', 'میلیاردی')
    text = text.replace('ملیارد', 'میلیارد')
    text = text.replace('ملیون', 'میلیون')
    text = text.replace('میلیونو', 'میلیون و')
    text = text.replace('هزارو', 'هزار و')
    
    # کلمات عددی فارسی
    word_numbers = {
        'صفر': 0, 'یک': 1, 'یه': 1, 'دو': 2, 'سه': 3, 'چهار': 4,
        'پنج': 5, 'شش': 6, 'شیش': 6, 'هفت': 7, 'هشت': 8, 'نه': 9,
        'ده': 10, 'یازده': 11, 'دوازده': 12, 'سیزده': 13,
        'چهارده': 14, 'پانزده': 15, 'پونزده': 15, 'شانزده': 16, 
        'هفده': 17, 'هجده': 18, 'هیجده': 18, 'نوزده': 19,
        'بیست': 20, 'سی': 30, 'چهل': 40, 'پنجاه': 50,
        'شصت': 60, 'هفتاد': 70, 'هشتاد': 80, 'نود': 90,
        'صد': 100, 'یکصد': 100, 'دویست': 200, 'سیصد': 300,
        'چهارصد': 400, 'پانصد': 500, 'پونصد': 500,
        'ششصد': 600, 'هفتصد': 700, 'هشتصد': 800, 'نهصد': 900,
    }

    # ضرایب بزرگ
    multipliers = {
        'هزار': 1_000,
        'میلیون': 1_000_000,
        'میلیارد': 1_000_000_000,
    }

    # === الگوریتم پردازش ===
    # جدا کردن با "و"
    text = text.replace(' و ', ' ')
    words = text.split()

    total = 0
    current_chunk = 0  # عدد فعلی قبل از ضریب
    
    i = 0
    while i < len(words):
        word = words[i].strip()
        
        if not word:
            i += 1
            continue
        
        # اگر عدد است
        if word in word_numbers:
            current_chunk += word_numbers[word]
        
        # اگر ضریب است
        elif word in multipliers:
            multiplier = multipliers[word]
            
            if current_chunk == 0:
                current_chunk = 1
            
            # ضرب در ضریب و اضافه به total
            total += current_chunk * multiplier
            current_chunk = 0
        
        # اگر عدد انگلیسی است
        else:
            try:
                num = float(word)
                current_chunk += num
            except ValueError:
                pass
        
        i += 1

    # اضافه کردن باقیمانده
    total += current_chunk

    if total > 0:
        logger.info(f"💰 persian_text_to_number: '{original_text}' -> {total:,.0f}")
        return float(total)
    
    return None

def _validate_and_normalize_input(pending_field: str, text) -> Tuple[bool, Optional[any]]:
    """اعتبارسنجی و نرمال‌سازی ورودی"""
    # اگر از قبل نرمال‌سازی شده (مثلاً بولی)، مستقیم برگردان
    if isinstance(text, bool):
        if pending_field in BOOLEAN_FIELDS:
            return True, text
        return False, None

    if not isinstance(text, str):
        text = str(text)

    clean_text = text.strip()

    # === فیلد نوع معامله ===
    if pending_field == "transaction_type":
        normalized = normalize_transaction_type(clean_text)
        if normalized:
            return True, normalized
        lower = clean_text.lower()
        if any(k in lower for k in ["فروش", "خرید", "sell", "sale"]):
            return True, "فروش"
        if any(k in lower for k in ["رهن", "اجاره", "rent", "کرایه"]):
            return True, "رهن و اجاره"
        if any(k in lower for k in ["پیش", "presale"]):
            return True, "پیش‌فروش"
        return False, None

    # === فیلد نوع ملک ===
    if pending_field == "property_type":
        normalized = normalize_property_type(clean_text)
        if normalized:
            return True, normalized
        return False, None

    # === فیلد نوع کاربری ===
    if pending_field == "usage_type":
        normalized = normalize_usage_type(clean_text)
        if normalized:
            return True, normalized
        return False, None

    # === فیلدهای عددی ===
    if pending_field in NUMERIC_FIELDS:
        val = text_to_int(clean_text)
        if val is not None and val > 0:
            return True, val
        return False, None

    # === فیلدهای قیمت ===
    if pending_field in PRICE_FIELDS:
        # ✅ اول سعی کن متن فارسی را تبدیل کنی
        persian_val = persian_text_to_number(clean_text)
        if persian_val is not None and persian_val > 0:
            return True, persian_val

        # سپس با text_to_int امتحان کن
        val = text_to_int(clean_text)
        if val is not None and val > 0:
            return True, val

        # در نهایت با normalize_price
        try:
            normalized = normalize_price(clean_text)
            if normalized and normalized > 0:
                return True, normalized
        except:
            pass
        return False, None

    
    # === فیلدهای بولی ===
    if pending_field in BOOLEAN_FIELDS:
        normalized = normalize_boolean_field(clean_text)
        if normalized is not None:
            return True, normalized
        return False, None
    
    # === فیلد شماره تلفن ===
    if pending_field == "owner_phone":
        normalized = normalize_iran_phone(clean_text)
        if normalized:
            return True, normalized
        return False, None
    
    # === فیلدهای متنی آزاد ===
    if pending_field in FREE_TEXT_FIELDS:
        # حداقل ۲ کاراکتر و حداکثر ۲۰۰ کاراکتر
        if 2 <= len(clean_text) <= 200:
            return True, clean_text
        return False, None
    
    # === سایر فیلدها (مثل neighborhood, owner_name) ===
    # حداقل ۲ کاراکتر و نباید عدد خالی باشد
    if len(clean_text) >= 2:
        # بررسی که فقط عدد نباشد (برای فیلدهای متنی)
        if not clean_text.isdigit():
            return True, clean_text
    
    return False, None


def _get_validation_error_message(pending_field: str) -> str:
    """پیام خطای اعتبارسنجی برای هر فیلد"""
    messages = {
        "transaction_type": "❌ لطفاً یکی از گزینه‌ها را انتخاب کنید:\n• فروش\n• رهن و اجاره\n• پیش‌فروش",
        "property_type": "❌ لطفاً نوع ملک را مشخص کنید:\n• آپارتمان\n• ویلا\n• زمین\n• مغازه",
        "usage_type": "❌ لطفاً نوع کاربری را مشخص کنید:\n• مسکونی\n• تجاری\n• اداری",
        "area": "❌ لطفاً متراژ را به عدد وارد کنید (مثال: 120)",
        "bedroom_count": "❌ لطفاً تعداد اتاق خواب را به عدد وارد کنید (مثال: 2)",
        "floor": "❌ لطفاً شماره طبقه را به عدد وارد کنید (مثال: 3)",
        "total_floors": "❌ لطفاً تعداد کل طبقات را به عدد وارد کنید (مثال: 5)",
        "unit_count": "❌ لطفاً تعداد واحد در طبقه را به عدد وارد کنید (مثال: 2)",
        "build_year": "❌ لطفاً سال ساخت را وارد کنید (مثال: 1402)",
        "price_total": "❌ لطفاً قیمت را به عدد وارد کنید (مثال: 5000000000 یا ۵ میلیارد)",
        "rent": "❌ لطفاً مبلغ اجاره را به عدد وارد کنید",
        "deposit": "❌ لطفاً مبلغ ودیعه را به عدد وارد کنید",
        "mortgage": "❌ لطفاً مبلغ رهن را به عدد وارد کنید",
        "has_elevator": "❌ لطفاً با 'بله' یا 'خیر' پاسخ دهید",
        "has_parking": "❌ لطفاً با 'بله' یا 'خیر' پاسخ دهید",
        "has_storage": "❌ لطفاً با 'بله' یا 'خیر' پاسخ دهید",
        "owner_phone": "❌ لطفاً شماره تلفن معتبر وارد کنید (مثال: 09121234567)",
        "owner_name": "❌ لطفاً نام مالک را وارد کنید (حداقل ۲ حرف)",
        "neighborhood": "❌ لطفاً نام محله را وارد کنید",
    }
    return messages.get(pending_field, "❌ ورودی نامعتبر است. لطفاً دوباره تلاش کنید.")


async def _process_pending_field(
    user_id: int,
    text: str,
    pending_field: str,
    extracted: Dict,
    update: Update
) -> bool:
    """
    پردازش ورودی برای فیلد pending با اعتبارسنجی
    Returns: True if handled, False otherwise
    """
    # ابتدا ورودی دکمه را نرمال‌سازی کن
    normalized_button = normalize_button_input(text)
    
    # اعتبارسنجی ورودی
    is_valid, normalized_value = _validate_and_normalize_input(pending_field, normalized_button)
    
    if not is_valid:
        # ورودی نامعتبر - پیام خطا بده و سوال را تکرار کن
        error_msg = _get_validation_error_message(pending_field)
        question = FIELD_QUESTIONS.get(pending_field, "لطفاً مقدار معتبر وارد کنید:")
        
        keyboard = get_reply_keyboard(pending_field)
        full_message = f"{error_msg}\n\n{question}"
        
        if keyboard:
            await update.message.reply_text(full_message, reply_markup=keyboard)
        else:
            await update.message.reply_text(full_message, reply_markup=ReplyKeyboardRemove())
        
        return True  # پردازش شد (با خطا)
    
    # ورودی معتبر - ذخیره کن
    extracted[pending_field] = normalized_value
    logger.info(f"✅ Valid input for {pending_field}: {normalized_value}")
    
    # پاک کردن pending field
    set_pending_field(user_id, None)
    
    return False  # ادامه پردازش عادی


async def process_text(text: str, user_id: int, update: Update):
    """تابع اصلی پردازش متن"""
    logger.info(f"INPUT from user {user_id}: {text}")
    
    # === حالت تایید ===
    if is_confirmation_mode(user_id):
        return await _handle_confirmation_mode(user_id, text, update)
    
    # === استخراج با LLM ===
    extracted = extract_json(text) or {}
    
    # === پردازش فیلد pending ===
    pending_field = get_pending_field(user_id)
    
    # === اگر pending_field داریم، مقادیر متناقض LLM را نادیده بگیر ===
    if pending_field:
        # حذف مقادیری که LLM اشتباه استخراج کرده
        numeric_fields = ['price_total', 'rent', 'deposit', 'area', 'floor', 'bedroom_count', 'total_floors', 'unit_count', 'build_year']
        text_fields = ['owner_name', 'neighborhood', 'city']
        
        fields_to_remove = []
        for cf in extracted.keys():
            if cf == pending_field:
                continue  # فیلد مورد انتظار را حذف نکن
            
            # اگر فیلد عددی است و pending_field هم عددی است
            if cf in numeric_fields:
                fields_to_remove.append(cf)
            # اگر فیلد متنی است و pending_field هم متنی است
            elif cf in text_fields and pending_field in text_fields:
                fields_to_remove.append(cf)
        
        for cf in fields_to_remove:
            logger.info(f"🚫 Ignoring LLM extraction of {cf}={extracted[cf]} while pending_field is {pending_field}")
            del extracted[cf]

        
        # پردازش ورودی pending
        handled = await _process_pending_field(
            user_id, text, pending_field, extracted, update
        )
        if handled:
            return  # خطای اعتبارسنجی - منتظر ورودی جدید


    
    # === نرمال‌سازی داده‌ها ===
    extracted = _normalize_extracted_data(extracted)
    
    # === ادغام با state ===
    current_state = get_state(user_id)
    
    # جلوگیری از بازنویسی property_type
    if current_state.get("property_type") and extracted.get("property_type"):
        del extracted["property_type"]
    
    # === Inference ===
    if not extracted.get("property_type") and not current_state.get("property_type"):
        extracted = infer_property_type(extracted)
    if not extracted.get("usage_type") and not current_state.get("usage_type"):
        extracted = infer_usage_type(extracted)
    extracted = normalize_location(extracted)
    
    # === ادغام state ===
    data = merge_state(user_id, extracted)
    data["_user_id"] = user_id
    logger.info(f"Merged state for user {user_id}: {data}")
    
    # === Rule Engine ===
    result = run_rule_engine(data)
    logger.info(f"Rule Engine Result: {result}")
    
    # === پاسخ به کاربر ===
    if result["status"] == "completed":
        set_confirmation_mode(user_id, True)
        confirmation_msg = format_confirmation_message(data)
        keyboard = ReplyKeyboardMarkup(
            [["✅ تایید", "✏️ ویرایش"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(confirmation_msg, reply_markup=keyboard)
    
    elif result.get("question"):
        pending = result.get("pending_field", result.get("missing"))
        keyboard = get_reply_keyboard(pending)
        
        if keyboard:
            await update.message.reply_text(result["question"], reply_markup=keyboard)
        else:
            await update.message.reply_text(result["question"], reply_markup=ReplyKeyboardRemove())
    
    else:
        await update.message.reply_text(
            "لطفاً اطلاعات ملک خود را ارسال کنید.",
            reply_markup=ReplyKeyboardRemove()
        )


def _normalize_extracted_data(extracted: Dict) -> Dict:
    """نرمال‌سازی داده‌های استخراج شده"""
    
    # نرمال‌سازی شماره تلفن
    if extracted.get("owner_phone"):
        extracted["owner_phone"] = normalize_iran_phone(extracted["owner_phone"])
    
    # نرمال‌سازی قیمت‌ها
    for price_key in PRICE_FIELDS:
        if extracted.get(price_key):
            try:
                extracted[price_key] = normalize_price(extracted[price_key])
            except:
                pass
    
    # اعتبارسنجی متراژ
    if extracted.get("area"):
        validated = validate_area(extracted["area"])
        if validated:
            extracted["area"] = validated
    
    # اعتبارسنجی طبقه
    if extracted.get("floor"):
        validated = validate_floor(extracted["floor"])
        if validated:
            extracted["floor"] = validated
    
    return extracted    # ✅ فقط ۴ فاصله



async def _handle_confirmation_mode(user_id: int, text: str, update: Update):
    """مدیریت تایید یا ویرایش نهایی اطلاعات"""
    from .handlers import handle_edit_request

    clean_text = (
        str(text)
        .replace("✅", "")
        .replace("❌", "")
        .replace("✏️", "")
        .strip()
        .lower()
    )

    # ✅ تایید نهایی
    if clean_text in {"تایید", "تأیید", "بله", "اره", "آره", "ok", "yes"}:
        state = get_state(user_id) or {}
        state.setdefault("user_telegram_id", str(user_id))

        confirmation_token = state.get("confirmation_token")
        if not confirmation_token:
            await update.message.reply_text(
                "❌ خطای سیستمی: توکن تایید یافت نشد.\n"
                "لطفاً مجدداً تلاش کنید."
            )
            return

        # 🛑 Idempotency Guard
        token_used = await is_confirmation_token_used(confirmation_token)
        if token_used:
            await update.message.reply_text(
                "✅ این آگهی قبلاً با موفقیت ثبت شده است.\n"
                "⚠️ ثبت مجدد انجام نشد."
            )
            clear_state(user_id)
            return

        credit_tx_id = None

        try:
            # 1️⃣ مصرف اعتبار
            credit_result = await consume_credit(
                telegram_id=str(user_id),
                amount=1,
                description="property_registration"
            )

            if not credit_result.get("success"):
                await update.message.reply_text(
                    "❌ اعتبار شما برای ثبت آگهی کافی نیست.\n"
                    "لطفاً بسته اعتباری خریداری کنید."
                )
                return

            credit_tx_id = credit_result.get("transaction_id")

            # 2️⃣ ثبت ملک
            resp = await create_property(
                user_telegram_id=user_id,
                property_data=state,
                confirmation_token=confirmation_token
            )

            logger.info(f"✅ Property created for user {user_id}: {resp}")

            clear_state(user_id)

            await update.message.reply_text(
                "✅ اطلاعات ملک با موفقیت ثبت شد!\n"
                "🙏 از همکاری شما متشکریم.",
                reply_markup=ReplyKeyboardRemove()
            )

        except Exception as e:
            logger.error(
                f"❌ Error saving property for user {user_id}: {e}",
                exc_info=True
            )

            # 🔄 Rollback اعتبار
            if credit_tx_id:
                await add_credit(
                    telegram_id=str(user_id),
                    amount=1,
                    reason="rollback_property_registration",
                    ref_transaction_id=credit_tx_id
                )

            await update.message.reply_text(
                "❌ ثبت ملک ناموفق بود.\n"
                "✅ اعتبار شما بازگردانده شد."
            )

        return

    # ✏️ درخواست ویرایش
    if clean_text == "ویرایش":
        current_state = get_state(user_id)
        summary = format_confirmation_message(current_state)

        keyboard = ReplyKeyboardMarkup(
            KEYBOARD_OPTIONS["confirmation"],
            resize_keyboard=True
        )

        await update.message.reply_text(
            f"{summary}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "✏️ برای ویرایش، فیلد را ارسال کنید:\n"
            "مثال:\n"
            "• متراژ: 120\n"
            "• قیمت: 5000000000\n"
            "• محله: گلسار",
            reply_markup=keyboard
        )
        return

    # ✏️ ویرایش متنی
    if await handle_edit_request(user_id, text, update):
        return

    # ❌ ورودی نامعتبر
    await update.message.reply_text(
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ تایید", "✏️ ویرایش"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )







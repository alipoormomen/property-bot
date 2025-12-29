# bot_processor_core/handlers.py
"""هندلرهای callback و ویرایش"""

import logging
import re
from telegram import Update, ReplyKeyboardMarkup

from conversation_state import get_state, merge_state, set_confirmation_mode
from bot_utils import format_confirmation_message
from utils import normalize_price
from phone_utils import normalize_iran_phone
from nocodb_client import create_property   
from .constants import KEYBOARD_OPTIONS, PRICE_FIELDS

logger = logging.getLogger(__name__)

# نگاشت نام فارسی به کلید فیلد
FIELD_NAME_MAP = {
    "نوع معامله": "transaction_type",
    "نوع ملک": "property_type",
    "کاربری": "usage_type",
    "متراژ": "area",
    "اتاق": "bedroom_count",          # ✅ اصلاح شد
    "خواب": "bedroom_count",           # ✅ اصلاح شد
    "تعداد خواب": "bedroom_count",     # ✅ اصلاح شد
    "اتاق خواب": "bedroom_count",      # ✅ اضافه شد
    "طبقه": "floor",
    "قیمت": "price_total",             # ✅ اصلاح شد
    "قیمت کل": "price_total",          # ✅ اصلاح شد
    "رهن": "deposit",                  # ✅ اصلاح شد (رهن = ودیعه)
    "ودیعه": "deposit",                # ✅ اضافه شد
    "اجاره": "rent",
    "محله": "neighborhood",
    "شهر": "city",
    "آدرس": "address",
    "نام مالک": "owner_name",
    "مالک": "owner_name",              # ✅ اضافه شد
    "تلفن": "owner_phone",
    "شماره تماس": "owner_phone",
    "شماره مالک": "owner_phone",       # ✅ اضافه شد
    "پارکینگ": "has_parking",
    "انباری": "has_storage",
    "آسانسور": "has_elevator",
    "بالکن": "has_balcony",
    "سال ساخت": "build_year",          # ✅ اصلاح شد
    "توضیحات": "additional_features",
    "ویژگی": "additional_features",
    "امکانات": "additional_features",  # ✅ اضافه شد - این خط مهم است!
    "ویژگی‌ها": "additional_features", # ✅ اضافه شد
    "تعداد طبقات": "total_floors",     # ✅ اضافه شد
    "کل طبقات": "total_floors",        # ✅ اضافه شد
    "واحد در طبقه": "unit_count",      # ✅ اضافه شد
}


async def handle_callback_query(update: Update, context=None):
    query = update.callback_query
    if not query:
        return

    await query.answer()
    user_id = query.from_user.id
    data = query.data

    logger.info(f"Callback query from {user_id}: {data}")

    if data.startswith("edit_"):
        field = data.replace("edit_", "")
        await query.message.reply_text(
            f"✏️ مقدار جدید برای «{field}» را وارد کنید:"
        )

    elif data == "confirm":
        from conversation_state import clear_state  # اگر بالای فایل import نکردی

        # ۱) گرفتن state فعلی کاربر
        state = get_state(user_id) or {}

        # ۲) اضافه‌کردن user_telegram_id اگر در state نیست
        state.setdefault("user_telegram_id", str(user_id))

        try:
            # ۳) ذخیره در NocoDB — تابع async است، حتماً await
            resp = await create_property(user_telegram_id=user_id, property_data=state)

            logger.info(f"Property created for user {user_id}: {resp}")

            # ۴) پاک‌کردن state بعد از ثبت موفق
            clear_state(user_id)

            await query.message.reply_text(
                "✅ اطلاعات ملک با موفقیت در سیستم ثبت شد.\n🙏 متشکریم."
            )

        except Exception as e:
            logger.error(f"Error while creating property for {user_id}: {e}", exc_info=True)
            await query.message.reply_text(
                "❌ در ثبت اطلاعات ملک در سیستم مشکل پیش آمد.\n"
                "لطفاً کمی بعد دوباره تلاش کنید یا اطلاعات را دوباره وارد کنید."
            )


    elif data == "cancel":
        from conversation_state import clear_state
        clear_state(user_id)
        await query.message.reply_text("❌ عملیات لغو شد.")

    else:
        logger.warning(f"Unknown callback data: {data}")


async def handle_edit_request(user_id: int, text: str, update: Update) -> bool:
    match = re.match(r'^(.+?)[:=]\s*(.+)$', text.strip())
    if not match:
        return False

    field_name = match.group(1).strip()
    new_value = match.group(2).strip()

    field_key = FIELD_NAME_MAP.get(field_name)
    if not field_key:
        for name, key in FIELD_NAME_MAP.items():
            if field_name in name or name in field_name:
                field_key = key
                break

    if not field_key:
        await update.message.reply_text(
            f"❌ فیلد «{field_name}» شناسایی نشد."
        )
        return True

    if field_key in PRICE_FIELDS:
        # ✅ اول سعی کن متن فارسی را تبدیل کنی
        from bot_processor_core.processor import persian_text_to_number
        persian_val = persian_text_to_number(new_value)
        if persian_val:
            new_value = persian_val
        else:
            nv = normalize_price(new_value)
            if nv:
                new_value = nv


    elif field_key == "owner_phone":
        phone = normalize_iran_phone(new_value)
        if phone:
            new_value = phone

    elif field_key.startswith("has_"):
        new_value = new_value.lower() in ["بله", "دارد", "yes", "true"]

    merge_state(user_id, {field_key: new_value})

    current_state = get_state(user_id)
    msg = format_confirmation_message(current_state)

    keyboard = ReplyKeyboardMarkup(
        KEYBOARD_OPTIONS["confirmation"],
        resize_keyboard=True
    )

    await update.message.reply_text(
        f"✅ «{field_name}» ویرایش شد.\n\n{msg}",
        reply_markup=keyboard
    )

    set_confirmation_mode(user_id, True)
    return True

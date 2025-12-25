# bot_processor_core/constants.py
"""ثابت‌ها، دکمه‌ها و مپ‌های تبدیل"""

KEYBOARD_OPTIONS = {
    "transaction_type": [["🏷 فروش", "🔑 رهن و اجاره"], ["🏗 پیش‌فروش"]],
    "property_type": [["🏢 آپارتمان", "🏡 ویلا"], ["🌍 زمین", "🏪 مغازه"]],
    "usage_type": [["🏠 مسکونی", "🏬 تجاری"], ["🏛 اداری"]],
    "has_parking": [["✅ بله", "❌ خیر"]],
    "has_elevator": [["✅ بله", "❌ خیر"]],
    "has_storage": [["✅ بله", "❌ خیر"]],
    "additional_features": [["ندارد"]],
    "confirmation": [["✅ تایید", "✏️ ویرایش"]],
}

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
    "✅ تایید": "تایید",
    "✏️ ویرایش": "ویرایش",
    "ندارد": "ندارد",
}

NUMERIC_FIELDS = [
    "area", "bedroom_count", "floor", "parking_count",
    "storage_count", "total_floors", "unit_count", "build_year"
]

PRICE_FIELDS = ["price_total", "rent", "deposit", "price", "mortgage"]

TEXT_FIELDS = ["owner_name", "neighborhood", "city", "address"]

# ✅ فیلدهای متن آزاد - هر ورودی قبول می‌شود و pending پاک می‌شود
FREE_TEXT_FIELDS = [
    "additional_features",
    "description",
    "notes",
    "owner_name",
    "neighborhood",
    "address",
    "city",
]

# ✅ سوالات هر فیلد
FIELD_QUESTIONS = {
    "transaction_type": "📋 نوع معامله را انتخاب کنید:",
    "property_type": "🏠 نوع ملک را انتخاب کنید:",
    "usage_type": "🎯 کاربری ملک را انتخاب کنید:",
    "area": "📐 متراژ ملک (بر حسب متر مربع):",
    "bedroom_count": "🛏 تعداد اتاق خواب:",
    "floor": "🔢 طبقه:",
    "total_floors": "🏗 تعداد کل طبقات ساختمان:",
    "build_year": "📅 سال ساخت:",
    "price": "💰 قیمت کل (تومان):",
    "price_total": "💰 قیمت کل (تومان):",
    "deposit": "💵 مبلغ رهن (تومان):",
    "rent": "💸 مبلغ اجاره ماهیانه (تومان):",
    "mortgage": "💵 مبلغ رهن (تومان):",
    "has_parking": "🚗 آیا پارکینگ دارد؟",
    "has_elevator": "🛗 آیا آسانسور دارد؟",
    "has_storage": "📦 آیا انباری دارد؟",
    "neighborhood": "📍 محله:",
    "city": "🌆 شهر:",
    "address": "🏠 آدرس کامل:",
    "owner_name": "👤 نام مالک:",
    "owner_phone": "📞 شماره تماس مالک:",
    "additional_features": "✨ ویژگی‌های اضافی (یا 'ندارد'):",
}

# ✅ ترتیب پرسش فیلدها
FIELD_ORDER = [
    "transaction_type",
    "property_type",
    "usage_type",
    "city",
    "neighborhood",
    "address",
    "area",
    "bedroom_count",
    "floor",
    "total_floors",
    "build_year",
    "price",           # برای فروش
    "price_total",     # برای فروش
    "deposit",         # برای رهن و اجاره
    "mortgage",        # برای رهن و اجاره
    "rent",            # برای رهن و اجاره
    "has_parking",
    "has_elevator",
    "has_storage",
    "owner_name",
    "owner_phone",
    "additional_features",
]

# ✅ نگاشت نام فارسی به کلید انگلیسی (برای ویرایش)
EDITABLE_FIELD_MAP = {
    "نوع معامله": "transaction_type",
    "نوع ملک": "property_type",
    "کاربری": "usage_type",
    "متراژ": "area",
    "اتاق": "bedroom_count",
    "خواب": "bedroom_count",
    "تعداد خواب": "bedroom_count",
    "طبقه": "floor",
    "کل طبقات": "total_floors",
    "سال ساخت": "build_year",
    "قیمت": "price",
    "قیمت کل": "price_total",
    "رهن": "deposit",
    "ودیعه": "deposit",
    "اجاره": "rent",
    "محله": "neighborhood",
    "شهر": "city",
    "آدرس": "address",
    "نام مالک": "owner_name",
    "تلفن": "owner_phone",
    "شماره تماس": "owner_phone",
    "پارکینگ": "has_parking",
    "انباری": "has_storage",
    "آسانسور": "has_elevator",
    "توضیحات": "additional_features",
    "ویژگی": "additional_features",
}

# فیلدهای مربوط به فروش
SALE_FIELDS = ["price", "price_total"]

# فیلدهای مربوط به رهن و اجاره
RENT_FIELDS = ["deposit", "mortgage", "rent"]

# فیلدهای بولین
BOOLEAN_FIELDS = ["has_parking", "has_elevator", "has_storage", "has_balcony"]

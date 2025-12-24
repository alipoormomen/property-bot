# messages.py

# --- EXTRACTOR ---
EXTRACTOR_SYSTEM_ROLE = "You are a real estate data extraction assistant."
EXTRACTOR_PROMPT_TEMPLATE = (
    "Extract real estate data from the following text:\n\n"
    "Text: \"{text}\"\n\n"
    "Return JSON with these fields (use null if not found):\n"
    "- transaction_type (Sale, Rent, Pre-sale)\n"
    "- property_type (Apartment, Villa, Land, Shop)\n"
    "- price_total (number)\n"
    "- rent (number)\n"
    "- area (number)\n"
    "- bedroom_count (number)\n"
    "- build_year (number)\n"
    "- floor (number)\n"
    "- total_floors (number)\n"
    "- unit_count (number)\n"
    "- has_parking (boolean)\n"
    "- parking_count (number)\n"
    "- has_elevator (boolean)\n"
    "- has_storage (boolean)\n"
    "- storage_count (number)\n"
    "- owner_name (string)\n"
    "- owner_phone (string)\n"
    "- neighborhood (string)\n"
)

# --- RULE ENGINE QUESTIONS ---
Q_TRANSACTION = "نوع معامله چیست؟ (فروش / رهن و اجاره / پیش‌فروش)"
Q_PROPERTY = "نوع ملک چیست؟ (آپارتمان / ویلایی / زمین / مغازه)"
Q_PHONE = "شماره تماس مالک را وارد کنید:"
Q_OWNER_NAME = "نام مالک چیست؟"
Q_PRICE_TOTAL = "قیمت کل (به تومان) چقدر است؟"
Q_DEPOSIT = "مبلغ رهن (به تومان) چقدر است؟"
Q_RENT = "مبلغ اجاره ماهانه (به تومان) چقدر است؟"
Q_AREA = "متراژ ملک چقدر است؟ (مثلاً ۱۲۰)"
Q_PARKING = "آیا پارکینگ دارد؟ (بله/خیر)"
Q_PARKING_COUNT = "تعداد پارکینگ؟"
Q_ELEVATOR = "آیا آسانسور دارد؟ (بله/خیر)"
Q_STORAGE = "آیا انباری دارد؟ (بله/خیر)"
Q_STORAGE_COUNT = "تعداد انباری؟"
Q_BEDROOM = "تعداد خواب؟"
MSG_COMPLETED = "اطلاعات تکمیل شد."

# --- PROCESSOR SUMMARY ---
MSG_UNKNOWN = "متوجه نشدم، لطفاً مجدد تلاش کنید."
MSG_SUMMARY_HEADER = "📋 خلاصه اطلاعات ملک:"
LBL_TRANSACTION = "نوع معامله"
LBL_PROPERTY = "نوع ملک"
LBL_PRICE = "قیمت کل"
LBL_RENT = "اجاره"
LBL_AREA = "متراژ"
LBL_BEDROOM = "تعداد خواب"
LBL_YEAR = "سال ساخت"
LBL_FLOOR = "طبقه"
LBL_TOTAL_FLOORS = "تعداد کل طبقات"
LBL_UNIT_COUNT = "تعداد واحد"
LBL_PHONE = "تلفن مالک"
LBL_NEIGHBORHOOD = "محله"

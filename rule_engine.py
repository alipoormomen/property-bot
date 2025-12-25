# -------------------------------------------------
# rule_engine.py (FINAL VERSION - بدون سوال شهر)
# ✅ شهر کلاً پرسیده نمی‌شود - فقط محله و سپس آدرس
# -------------------------------------------------

import logging
from typing import Dict, Optional
from conversation_state import set_pending_field

logger = logging.getLogger(__name__)

def run_rule_engine(data: Dict) -> Dict:
    """
    ✅ Rule Engine نهایی - بدون سوال شهر
    Flow: Transaction → Type → [Details] → Specs → Price → Neighborhood → Address → Owner
    """
    user_id = data.get("_user_id")

    # ============================================
    # 1️⃣ نوع معامله
    # ============================================
    if data.get("transaction_type") is None:
        set_pending_field(user_id, "transaction_type")
        return {
            "status": "ask",
            "missing": "transaction_type",
            "question": "🏷 قصد چه کاری دارید؟ (فروش / رهن و اجاره)",
        }

    # ============================================
    # 2️⃣ نوع ملک
    # ============================================
    if data.get("property_type") is None:
        set_pending_field(user_id, "property_type")
        return {
            "status": "ask",
            "missing": "property_type",
            "question": "🏠 نوع ملک چیست؟ (آپارتمان، ویلا، زمین، مغازه)",
        }

    # ============================================
    # 3️⃣ سوالات ویژه آپارتمان
    # ============================================
    if data.get("property_type") in ["آپارتمان", "Apartment", "اپارتمان"]:

        # 3.1 نوع کاربری
        if data.get("usage_type") is None:
            set_pending_field(user_id, "usage_type")
            return {
                "status": "ask",
                "missing": "usage_type",
                "question": "🏢 نوع کاربری چیست؟ (مسکونی / تجاری / اداری)",
            }

        # 3.2 متراژ
        if data.get("area") is None:
            set_pending_field(user_id, "area")
            return {
                "status": "ask",
                "missing": "area",
                "question": "📐 متراژ ملک چقدر است؟",
            }

        # 3.3 تعداد اتاق خواب (فقط مسکونی)
        if data.get("usage_type") in ["مسکونی", "Residential"]:
            if data.get("bedroom_count") is None:
                set_pending_field(user_id, "bedroom_count")
                return {
                    "status": "ask",
                    "missing": "bedroom_count",
                    "question": "🛏 چند خواب دارد؟",
                }

        # 3.4 تعداد کل طبقات ساختمان
        if data.get("total_floors") is None:
            set_pending_field(user_id, "total_floors")
            return {
                "status": "ask",
                "missing": "total_floors",
                "question": "🏢 ساختمان چند طبقه است؟",
            }

        # 3.5 واحد در کدام طبقه
        if data.get("floor") is None:
            set_pending_field(user_id, "floor")
            return {
                "status": "ask",
                "missing": "floor",
                "question": "📍 واحد در چه طبقه‌ای است؟",
            }

        # 3.6 تعداد واحد در هر طبقه
        if data.get("unit_count") is None:
            set_pending_field(user_id, "unit_count")
            return {
                "status": "ask",
                "missing": "unit_count",
                "question": "🚪 هر طبقه چند واحد دارد؟",
            }

        # 3.7 آسانسور
        if data.get("has_elevator") is None:
            set_pending_field(user_id, "has_elevator")
            return {
                "status": "ask",
                "missing": "has_elevator",
                "question": "🛗 آسانسور دارد؟ (بله / خیر)",
            }

        # 3.8 سال ساخت
        if data.get("build_year") is None:
            set_pending_field(user_id, "build_year")
            return {
                "status": "ask",
                "missing": "build_year",
                "question": "📅 سال ساخت چه سالی است؟ (مثلاً 1402 یا نوساز)",
            }

    # ============================================
    # 4️⃣ سوالات عمومی (ویلا، زمین، مغازه)
    # ============================================
    else:
        # متراژ
        if data.get("area") is None:
            set_pending_field(user_id, "area")
            return {
                "status": "ask",
                "missing": "area",
                "question": "📐 متراژ ملک چقدر است؟",
            }

        # برای ویلا: تعداد خواب
        if data.get("property_type") in ["ویلا", "Villa", "ویلایی"]:
            if data.get("bedroom_count") is None:
                set_pending_field(user_id, "bedroom_count")
                return {
                    "status": "ask",
                    "missing": "bedroom_count",
                    "question": "🛏 ویلا چند خواب دارد؟",
                }

    # ============================================
    # 5️⃣ قیمت
    # ============================================
    if data.get("transaction_type") in ["فروش", "Sale", "پیش‌فروش"]:
        if data.get("price_total") is None and data.get("price") is None:
            set_pending_field(user_id, "price_total")
            return {
                "status": "ask",
                "missing": "price_total",
                "question": "💰 قیمت کل چقدر است؟",
            }

    if data.get("transaction_type") in ["رهن و اجاره", "Rent", "اجاره", "رهن"]:
        if data.get("price_total") is None:
            set_pending_field(user_id, "price_total")
            return {
                "status": "ask",
                "missing": "price_total",
                "question": "💰 مبلغ رهن (ودیعه) چقدر است؟",
            }
        if data.get("rent") is None:
            set_pending_field(user_id, "rent")
            return {
                "status": "ask",
                "missing": "rent",
                "question": "💵 اجاره ماهیانه چقدر است؟",
            }

    # ============================================
    # 6️⃣ محله (بدون سوال شهر!)
    # ============================================
    if data.get("neighborhood") is None:
        set_pending_field(user_id, "neighborhood")
        return {
            "status": "ask",
            "missing": "neighborhood",
            "question": "📍 ملک در کدام محله/منطقه است؟",
        }

    # ============================================
    # 7️⃣ آدرس دقیق (جدید - بعد از محله)
    # ============================================
    if data.get("address") is None:
        set_pending_field(user_id, "address")
        return {
            "status": "ask",
            "missing": "address",
            "question": "🏠 آدرس دقیق ملک را وارد کنید:\n(مثال: رشت، گلسار، خیابان ۱۰۷)",
        }

    # ============================================
    # 8️⃣ اطلاعات مالک
    # ============================================
    if data.get("owner_name") is None:
        set_pending_field(user_id, "owner_name")
        return {
            "status": "ask",
            "missing": "owner_name",
            "question": "👤 نام شریف شما؟",
        }

    if data.get("owner_phone") is None:
        set_pending_field(user_id, "owner_phone")
        return {
            "status": "ask",
            "missing": "owner_phone",
            "question": "📞 لطفاً شماره تماس خود را وارد کنید:",
        }

    # ============================================
    # ✅ تکمیل شد!
    # ============================================
    set_pending_field(user_id, None)
    return {
        "status": "completed",
        "message": "✅ اطلاعات کامل شد."
    }

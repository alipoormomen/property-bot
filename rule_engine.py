# rule_engine.py - COMPLETE FIXED VERSION
import logging
from typing import Dict
from conversation_state import set_pending_field

logger = logging.getLogger(__name__)


def run_rule_engine(data: Dict) -> Dict:
    """
    Rule Engine با 8 مرحله کامل
    Flow: Transaction → Type → Details → Price → Location → Owner → Features → Complete
    """
    user_id = data.get("_user_id")

    # ============================================
    # 1️⃣ نوع معامله
    # ============================================
    if data.get("transaction_type") is None:
        set_pending_field(user_id, "transaction_type")
        return {
            "status": "question",
            "missing": "transaction_type",
            "question": "🏷 قصد چه کاری دارید؟ (فروش / رهن و اجاره)",
        }

    # ============================================
    # 2️⃣ نوع ملک
    # ============================================
    if data.get("property_type") is None:
        set_pending_field(user_id, "property_type")
        return {
            "status": "question",
            "missing": "property_type",
            "question": "🏠 نوع ملک چیست؟ (آپارتمان، ویلا، زمین، مغازه)",
        }

    # ============================================
    # 3️⃣ سوالات ویژه آپارتمان
    # ============================================
    if data.get("property_type") in ["آپارتمان", "Apartment"]:

        if data.get("usage_type") is None:
            set_pending_field(user_id, "usage_type")
            return {
                "status": "question",
                "missing": "usage_type",
                "question": "🏢 نوع کاربری چیست؟ (مسکونی / تجاری / اداری)",
            }

        if data.get("area") is None:
            set_pending_field(user_id, "area")
            return {
                "status": "question",
                "missing": "area",
                "question": "📐 متراژ ملک چقدر است؟",
            }

        if data.get("usage_type") in ["مسکونی", "Residential"]:
            if data.get("bedroom_count") is None:
                set_pending_field(user_id, "bedroom_count")
                return {
                    "status": "question",
                    "missing": "bedroom_count",
                    "question": "🛏 چند خواب دارد؟",
                }

        if data.get("total_floors") is None:
            set_pending_field(user_id, "total_floors")
            return {
                "status": "question",
                "missing": "total_floors",
                "question": "🏢 ساختمان چند طبقه است؟",
            }

        if data.get("floor") is None:
            set_pending_field(user_id, "floor")
            return {
                "status": "question",
                "missing": "floor",
                "question": "📍 واحد در چه طبقه‌ای است؟",
            }

        if data.get("unit_count") is None:
            set_pending_field(user_id, "unit_count")
            return {
                "status": "question",
                "missing": "unit_count",
                "question": "🚪 هر طبقه چند واحد دارد؟",
            }

        if data.get("has_elevator") is None:
            set_pending_field(user_id, "has_elevator")
            return {
                "status": "question",
                "missing": "has_elevator",
                "question": "🛗 آسانسور دارد؟ (بله / خیر)",
            }

        if data.get("build_year") is None:
            set_pending_field(user_id, "build_year")
            return {
                "status": "question",
                "missing": "build_year",
                "question": "📅 سال ساخت چه سالی است؟ (مثلاً 1402)",
            }

    # ============================================
    # 4️⃣ سوالات عمومی (ویلا، زمین، مغازه)
    # ============================================
    else:
        if data.get("area") is None:
            set_pending_field(user_id, "area")
            return {
                "status": "question",
                "missing": "area",
                "question": "📐 متراژ ملک چقدر است؟",
            }

        if data.get("property_type") in ["ویلا", "Villa", "ویلایی"]:
            if data.get("bedroom_count") is None:
                set_pending_field(user_id, "bedroom_count")
                return {
                    "status": "question",
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
                "status": "question",
                "missing": "price_total",
                "question": "💰 قیمت کل چقدر است؟",
            }

    if data.get("transaction_type") in ["رهن و اجاره", "Rent", "اجاره"]:
        if data.get("price_total") is None:
            set_pending_field(user_id, "price_total")
            return {
                "status": "question",
                "missing": "price_total",
                "question": "💰 مبلغ رهن (ودیعه) چقدر است؟",
            }
        if data.get("rent") is None:
            set_pending_field(user_id, "rent")
            return {
                "status": "question",
                "missing": "rent",
                "question": "💵 اجاره ماهیانه چقدر است؟",
            }

    # ============================================
    # 6️⃣ محله/آدرس
    # ============================================
    if data.get("neighborhood") is None and data.get("city") is None:
        set_pending_field(user_id, "neighborhood")
        return {
            "status": "question",
            "missing": "neighborhood",
            "question": "📍 ملک در کدام محله/منطقه است؟",
        }

    # ============================================
    # 7️⃣ اطلاعات مالک
    # ============================================
    if data.get("owner_name") is None:
        set_pending_field(user_id, "owner_name")
        return {
            "status": "question",
            "missing": "owner_name",
            "question": "👤 نام شریف شما؟",
        }

    if data.get("owner_phone") is None:
        set_pending_field(user_id, "owner_phone")
        return {
            "status": "question",
            "missing": "owner_phone",
            "question": "📞 لطفاً شماره تماس خود را وارد کنید:",
        }

    # ============================================
    # 8️⃣ امکانات اضافی
    # ============================================
    if not data.get("additional_features_collected"):
        set_pending_field(user_id, "additional_features")
        return {
            "status": "question",
            "missing": "additional_features",
            "question": "🏊 آیا امکانات خاصی دارد؟ (مثلا: لابی، استخر، سونا، نگهبان)\nاگر ندارد بنویسید: ندارد",
        }

    # ============================================
    # ✅ تکمیل شد
    # ============================================
    set_pending_field(user_id, None)
    return {
        "status": "completed",
        "message": "✅ اطلاعات کامل شد.",
    }

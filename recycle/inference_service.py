# services/inference_service.py

def infer_property_type(data: dict) -> dict:
    """
    استنباط نوع ملک از روی اطلاعات موجود
    """
    if data.get("property_type"):
        return data

    floor = data.get("floor")
    if floor is not None:
        data["property_type"] = "آپارتمان"

    return data


def infer_usage_type(data: dict) -> dict:
    """
    استنباط نوع کاربری (مسکونی/تجاری)
    """
    if data.get("usage_type"):
        return data

    text = " ".join(
        str(v) for v in data.values() if isinstance(v, str)
    )

    if any(k in text for k in ["تجاری", "مغازه", "پاساژ"]):
        data["usage_type"] = "تجاری"
    elif any(k in text for k in ["مسکونی", "خانه", "آپارتمان"]):
        data["usage_type"] = "مسکونی"

    return data


def normalize_location(data: dict) -> dict:
    """
    ✅ CRITICAL FIX: جلوگیری از لوپ محله
    - اگر street پر است ولی neighborhood خالی، street را به neighborhood انتقال بده
    - اگر محله وجود دارد ولی شهر نیست، شهر را "رشت" قرار بده
    """

    # ✅ FIX 1: اگر street داریم ولی neighborhood نداریم
    if data.get("street") and not data.get("neighborhood"):
        data["neighborhood"] = data["street"]

    # منابع متنی برای استخراج
    text_sources = [
        data.get("location", ""),
        data.get("address", ""),
        data.get("full_address", ""),
        data.get("raw_text", ""),
        data.get("address_text", ""),  # ✅ اضافه شد
    ]
    full_text = " ".join(text_sources)

    # --- CITY ---
    if data.get("city") is None:
        # ✅ اگر محله داریم، شهر را رشت فرض می‌کنیم
        if data.get("neighborhood"):
            data["city"] = "رشت"
        else:
            # اگر محله نداریم، از متن تشخیص بده
            known_cities = ["رشت", "تهران", "مشهد", "اصفهان", "شیراز", "تبریز"]
            for city in known_cities:
                if city in full_text:
                    data["city"] = city
                    break

    # --- NEIGHBORHOOD ---
    if data.get("neighborhood") is None:
        # محله‌های شناخته شده رشت
        known_neighborhoods = ["معلم", "گلسار", "سنگ", "مطهری", "خیابان امام", "لاکانی"]
        
        for neighborhood in known_neighborhoods:
            if neighborhood in full_text:
                data["neighborhood"] = neighborhood
                break
        
        # اگر هنوز پیدا نشد، کلمات کلیدی را بررسی کن
        if data.get("neighborhood") is None:
            keywords = ["محله", "خیابان", "بلوار"]
            for kw in keywords:
                if kw in full_text:
                    try:
                        part = full_text.split(kw, 1)[1]
                        name = part.strip().split()[0]
                        if len(name) > 2:
                            data["neighborhood"] = name
                            break
                    except Exception:
                        pass

    return data

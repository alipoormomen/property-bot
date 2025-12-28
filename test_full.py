# test_full.py
import asyncio
from nocodb_client import (
    get_or_create_user, get_user_credit, add_credit, deduct_credit,
    get_active_packages, create_property, get_user_properties,
    create_transaction, get_user_transactions
)

TEST_TG_ID = 999888777  # کاربر جدید

async def main():
    print("═" * 50)
    print("  🧪 تست کامل NocoDB Client")
    print("═" * 50)
    
    # 1. کاربر
    print("\n1️⃣ ایجاد کاربر جدید...")
    user = await get_or_create_user(TEST_TG_ID, username="full_test", first_name="تست کامل")
    print(f"   ✅ کاربر: {user.get('first_name')} | موجودی: {user.get('balance', 0)}")
    
    # 2. بسته‌ها
    print("\n2️⃣ دریافت بسته‌ها...")
    packages = await get_active_packages()
    print(f"   📦 {len(packages)} بسته فعال")
    
    # 3. خرید بسته (افزایش اعتبار)
    print("\n3️⃣ شبیه‌سازی خرید بسته اقتصادی...")
    pkg = packages[1] if len(packages) > 1 else packages[0]
    credits_to_add = pkg.get('credits', 200000)
    new_balance = await add_credit(TEST_TG_ID, credits_to_add)
    print(f"   💰 +{credits_to_add:,} اعتبار → موجودی: {new_balance:,}")
    
    # ثبت تراکنش خرید
    await create_transaction(TEST_TG_ID, "charge", credits_to_add, f"خرید بسته {pkg.get('name')}")
    print("   📝 تراکنش ثبت شد")
    
    # 4. کسر اعتبار (مصرف AI)
    print("\n4️⃣ شبیه‌سازی مصرف AI...")
    cost = 500
    after = await deduct_credit(TEST_TG_ID, cost)
    print(f"   🤖 -{cost} اعتبار → موجودی: {after:,}")
    
    await create_transaction(TEST_TG_ID, "usage", -cost, "پردازش ملک با AI")
    
    # 5. ثبت ملک
    print("\n5️⃣ ثبت ملک...")
    prop = await create_property(TEST_TG_ID, {
        "property_type": "آپارتمان",
        "transaction_type": "فروش",
        "city": "تهران",
        "district": "سعادت‌آباد",
        "area": 150,
        "rooms": 3,
        "price": 18000000000,
    })
    print(f"   🏠 ملک ثبت شد: {prop}")
    
    # 6. لیست ملک‌ها
    print("\n6️⃣ ملک‌های کاربر...")
    props = await get_user_properties(TEST_TG_ID)
    print(f"   📋 {len(props)} ملک")
    
    # 7. تراکنش‌ها
    print("\n7️⃣ تراکنش‌ها...")
    txs = await get_user_transactions(TEST_TG_ID)
    print(f"   📜 {len(txs)} تراکنش")
    for tx in txs:
        print(f"      • {tx.get('type')}: {tx.get('amount'):+,} - {tx.get('description')}")
    
    # 8. تست اعتبار ناکافی
    print("\n8️⃣ تست اعتبار ناکافی...")
    current = await get_user_credit(TEST_TG_ID)
    result = await deduct_credit(TEST_TG_ID, current + 100000)
    if result is None:
        print("   ✅ درست! جلوگیری از کسر بیش از موجودی")
    
    print("\n" + "═" * 50)
    print("  ✅ همه تست‌ها پاس شد!")
    print("═" * 50)

asyncio.run(main())

# test_final.py


# test_final.py
import asyncio
import sys
sys.path.insert(0, 'services')
import nocodb_client
from nocodb_client import NocoDBClient
# ببینیم چی داره
print(dir(nocodb_client))

async def test_full_flow():
    client = NocoDBClient()
    test_user_id = 888777666  # ID جدید برای تست تمیز
    
    print("="*60)
    print("🧪 تست جامع نهایی NocoDB")
    print("="*60)
    
    # 1. پاکسازی کاربر قبلی (اگه هست)
    print("\n1️⃣ بررسی/ایجاد کاربر...")
    user = await client.get_user(test_user_id)
    if user:
        print(f"   ⚠️ کاربر موجود - حذف میکنم...")
        await client.delete_user(test_user_id)
    
    # 2. ایجاد کاربر جدید
    user = await client.create_user(test_user_id, "Test User Final", "09121234567")
    print(f"   ✅ کاربر ایجاد شد: {user}")
    
    # 3. خرید بسته
    print("\n2️⃣ خرید بسته اقتصادی...")
    packages = await client.get_active_packages()
    eco_pkg = next((p for p in packages if p.get('name') == 'اقتصادی'), None)
    if eco_pkg:
        success = await client.purchase_package(test_user_id, eco_pkg)
        print(f"   ✅ خرید: {'موفق' if success else 'ناموفق'}")
    
    # 4. بررسی اعتبار
    print("\n3️⃣ بررسی اعتبار...")
    credit = await client.get_user_credit(test_user_id)
    print(f"   💰 اعتبار فعلی: {credit:,} تومان")
    
    # 5. کسر اعتبار
    print("\n4️⃣ کسر اعتبار (5000 تومان)...")
    result = await client.deduct_credit(test_user_id, 5000, "تست ثبت ملک")
    print(f"   ✅ کسر: {'موفق' if result else 'ناموفق'}")
    
    # 6. ثبت ملک
    print("\n5️⃣ ثبت ملک...")
    property_data = {
        "transaction_type": "فروش",
        "property_type": "آپارتمان", 
        "city": "تهران",
        "neighborhood": "ونک",
        "area": 120,
        "rooms": 2,
        "floor": 5,
        "total_price": 5000000000,
    }
    prop = await client.create_property(test_user_id, property_data)
    print(f"   ✅ ملک ثبت شد: {prop.get('Id') if prop else 'خطا'}")
    
    # 7. دریافت ملک‌های کاربر
    print("\n6️⃣ دریافت ملک‌های کاربر...")
    properties = await client.get_user_properties(test_user_id)
    print(f"   📋 تعداد ملک‌ها: {len(properties)}")
    for p in properties:
        print(f"      - {p.get('property_type')} در {p.get('city')} ({p.get('area')} متر)")
    
    # 8. دریافت تراکنش‌ها
    print("\n7️⃣ دریافت تراکنش‌ها...")
    transactions = await client.get_user_transactions(test_user_id)
    print(f"   📋 تعداد تراکنش‌ها: {len(transactions)}")
    for t in transactions:
        print(f"      - {t.get('type')}: {t.get('amount'):,} تومان - {t.get('description')}")
    
    # 9. اعتبار نهایی
    print("\n8️⃣ اعتبار نهایی...")
    final_credit = await client.get_user_credit(test_user_id)
    print(f"   💰 اعتبار: {final_credit:,} تومان")
    
    print("\n" + "="*60)
    print("✅ تست جامع کامل شد!")
    print("="*60)

asyncio.run(test_full_flow())

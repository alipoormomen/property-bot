import logging
import time
from processor import process_user_input
from conversation_state import clear_state

# تنظیمات لاگ
logging.basicConfig(level=logging.ERROR)

def run_test():
    user_id = 8888
    print("--- شروع تست ---")
    
    # پاک کردن حافظه قبلی
    clear_state(user_id)

    # سناریوی مکالمه
    steps = [
        "سلام یک آپارتمان برای فروش دارم",
        "در خیابان معلم رشت",
        "قیمتش ۵ میلیارد تومان",
        "۱۲۰ متره",
        "سال ساخت ۱۴۰۰",
        "۵ طبقه است",
        "طبقه سوم",
        "هر طبقه ۲ واحد",
        "۳ خواب داره",
        "پارکینگ دارد",
        "۱ پارکینگ",
        "آسانسور داره",
        "انباری هم داره",
        "۱ انباری",
        "اسمم علی رضایی",
        "شماره تماسم 09123456789"
    ]

    for i, text in enumerate(steps, 1):
        print(f"\n👤 کاربر: {text}")
        
        # ارسال به پردازشگر
        response = process_user_input(text, user_id)
        
        print(f"🤖 ربات: {response}")
        
        if "اطلاعات کامل شد" in response:
            print("\n🎉 تست با موفقیت تمام شد!")
            break
        
        time.sleep(1)

if __name__ == "__main__":
    run_test()

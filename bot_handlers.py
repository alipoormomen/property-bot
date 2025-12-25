# bot_handlers.py - Telegram Message Handlers
import logging
import traceback
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from stt import voice_to_text
from bot_processor import process_text
from conversation_state import clear_state

logger = logging.getLogger(__name__)

# ✅ پیام استارت جدید
START_MESSAGE = """👋 سلام! برای ثبت ملک خود، اطلاعات را صوتی 🎤 یا متنی⌨️ ارسال کنید.

---
✅ چه اطلاعاتی نیاز است؟
• نوع معامله (فروش، رهن و اجاره، پیش‌فروش)
• نوع ملک (آپارتمان، ویلا، زمین، مغازه)
• متراژ و تعداد خواب
• قیمت (برای فروش) یا رهن و اجاره (برای اجاره)
• محله و شهر
• نام و شماره تماس

برای آپارتمان، سوالات تکمیلی دیگری نیز پرسیده می‌شود."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    clear_state(user_id)
    await update.message.reply_text(START_MESSAGE, reply_markup=ReplyKeyboardRemove())

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    if not update.message.voice:
        return

    await update.message.reply_text("در حال پردازش صدا...")

    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        text = await voice_to_text(file)

        if text:
            await process_text(text, update.effective_user.id, update)
        else:
            await update.message.reply_text("متاسفانه صدا نامفهوم بود. لطفا مجددا تلاش کنید.")

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        await update.message.reply_text("خطا در پردازش صدا. لطفا مجددا تلاش کنید.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    if update.message.text:
        try:
            await process_text(update.message.text, update.effective_user.id, update)
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            logger.error(traceback.format_exc())
            await update.message.reply_text("❌ خطا در پردازش پیام. لطفا مجددا تلاش کنید.")

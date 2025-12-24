# handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from processor import process_user_input
from messages import START_MESSAGE, format_property_summary
from stt import voice_to_text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(START_MESSAGE)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
text = update.message.text
await _process_and_reply(update, text, user_id)

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
file = await context.bot.get_file(update.message.voice.file_id)

msg = await update.message.reply_text("🎧 در حال تبدیل صدا به متن...")
text = await voice_to_text(file)

if not text:
await msg.edit_text("❌ متاسفانه صدا واضح نبود.")
return

await msg.edit_text(f"🗣 متن تشخیص داده شده:\n\"{text}\"")
await _process_and_reply(update, text, user_id)

async def _process_and_reply(update: Update, text: str, user_id: int):
"""تابع کمکی مشترک برای متن و ویس"""
try:
result = await process_user_input(text, user_id)

rule_status = result["rule_result"]
data = result["data"]

if rule_status["status"] == "question":
# سوال بعدی را بپرس
await update.message.reply_text(f"🤔 {rule_status['question']}")

elif rule_status["status"] == "completed":
# نمایش خلاصه نهایی
summary = format_property_summary(data)
await update.message.reply_text(f"🎉 اطلاعات کامل شد!\n\n{summary}")
# اینجا می‌توان تابع save_to_db را فراخوانی کرد

except Exception as e:
await update.message.reply_text("❌ خطایی در پردازش رخ داد.")
print(f"Error: {e}")

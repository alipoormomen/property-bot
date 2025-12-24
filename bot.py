# bot.py - Main Entry Point
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, PROXY_URL
from bot_handlers import handle_voice, handle_text, start

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main():
    """Main bot runner"""
    request = HTTPXRequest(
        proxy=PROXY_URL,
        http_version="1.1",
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0
    )
    
    logger.info(f"Bot starting with Proxy: {PROXY_URL}")
    
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
        
        # Register handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        print("Bot is ready. Waiting for messages...")
        app.run_polling(close_loop=False)
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    main()

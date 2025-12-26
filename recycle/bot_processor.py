# bot_processor.py - Re-exporter (نقطه ورود اصلی)
"""
این فایل فقط برای سازگاری با کدهای موجود است.
تمام منطق به bot_processor_core منتقل شده.
"""

from bot_processor_core import (
    process_text,
    handle_edit_request,
    handle_callback_query,
    KEYBOARD_OPTIONS,
    BUTTON_VALUE_MAP,
    get_reply_keyboard,
    normalize_button_input,
)

__all__ = [
    "process_text",
    "handle_edit_request",
    "handle_callback_query",
    "KEYBOARD_OPTIONS",
    "BUTTON_VALUE_MAP",
    "get_reply_keyboard",
    "normalize_button_input",
]

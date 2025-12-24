# conversation_state.py
# ✅ COMPLETE VERSION - با Confirmation & Edit Flow

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_states: Dict[int, Dict] = {}
_state_timestamps: Dict[int, datetime] = {}

STATE_TTL_MINUTES = 60

def _cleanup_old_states():
    now = datetime.now()
    expired_users = []

    for user_id, timestamp in _state_timestamps.items():
        if now - timestamp > timedelta(minutes=STATE_TTL_MINUTES):
            expired_users.append(user_id)

    for user_id in expired_users:
        if user_id in _states:
            del _states[user_id]
        if user_id in _state_timestamps:
            del _state_timestamps[user_id]
        logger.info(f"[STATE EXPIRED] user_id={user_id}")

def merge_state(user_id: int, new_data: Dict) -> Dict:
    _cleanup_old_states()

    if user_id not in _states:
        _states[user_id] = {}

    _state_timestamps[user_id] = datetime.now()

    for key, value in new_data.items():
        if value is not None:
            _states[user_id][key] = value

    return _states[user_id]

def get_state(user_id: int) -> Dict:
    _cleanup_old_states()
    return _states.get(user_id, {})

def clear_state(user_id: int):
    if user_id in _states:
        del _states[user_id]
    if user_id in _state_timestamps:
        del _state_timestamps[user_id]
    logger.info(f"[STATE CLEARED] user_id={user_id}")

# ✅ Confirmation Mode
def set_confirmation_mode(user_id: int, enabled: bool):
    if user_id not in _states:
        _states[user_id] = {}
    _states[user_id]["_confirmation_mode"] = enabled
    _state_timestamps[user_id] = datetime.now()

def is_confirmation_mode(user_id: int) -> bool:
    if user_id not in _states:
        return False
    return _states[user_id].get("_confirmation_mode", False)

# ✅ Editing Field
def set_editing_field(user_id: int, field: Optional[str]):
    if user_id not in _states:
        _states[user_id] = {}
    _states[user_id]["_editing_field"] = field
    _state_timestamps[user_id] = datetime.now()

def get_editing_field(user_id: int) -> Optional[str]:
    if user_id not in _states:
        return None
    return _states[user_id].get("_editing_field")

# ✅ Pending Field (برای Rule Engine)
def set_pending_field(user_id: int, field_name: Optional[str]):
    if user_id not in _states:
        _states[user_id] = {}
    _states[user_id]["_pending_field"] = field_name
    _state_timestamps[user_id] = datetime.now()
    
    if field_name:
        logger.info(f"⏳ Set pending field: {field_name} for user {user_id}")
    else:
        logger.info(f"🧹 Cleared pending field for user {user_id}")

def get_pending_field(user_id: int) -> Optional[str]:
    if user_id not in _states:
        return None
    return _states[user_id].get("_pending_field")

def get_state_statistics() -> Dict:
    _cleanup_old_states()
    return {
        "total_users": len(_states),
        "ttl_minutes": STATE_TTL_MINUTES,
        "active_users": list(_states.keys())
    }

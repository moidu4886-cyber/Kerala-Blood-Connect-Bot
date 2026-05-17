"""
keyboards.py — All InlineKeyboard layouts for Kerala Blood Connect Bot
Uses aiogram 3 InlineKeyboardBuilder for clean, reusable keyboard construction.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BLOOD_GROUPS, KERALA_DISTRICTS, URGENCY_LEVELS


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🩸 Register as Donor", callback_data="register"))
    builder.row(InlineKeyboardButton(text="🔍 Find Blood Donor", callback_data="find_blood"))
    builder.row(InlineKeyboardButton(text="🚨 Emergency Request", callback_data="emergency"))
    builder.row(InlineKeyboardButton(text="👤 My Profile", callback_data="my_profile"))
    builder.row(
        InlineKeyboardButton(text="✅ Update Availability", callback_data="toggle_availability"),
        InlineKeyboardButton(text="✏️ Edit Profile",       callback_data="edit_profile"),
    )
    builder.row(InlineKeyboardButton(text="📢 Share Bot",  callback_data="share_bot"))
    builder.row(InlineKeyboardButton(text="❓ Help",        callback_data="help"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# BLOOD GROUP SELECTOR
# ─────────────────────────────────────────────────────────────────────────────

def blood_group_keyboard(prefix: str = "bg") -> InlineKeyboardMarkup:
    """
    prefix is used to differentiate callbacks:
      'bg'  → registration flow
      'sbg' → search flow
      'ebg' → emergency flow
    """
    builder = InlineKeyboardBuilder()
    for bg in BLOOD_GROUPS:
        builder.button(text=f"🩸 {bg}", callback_data=f"{prefix}:{bg}")
    builder.adjust(4)
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# DISTRICT SELECTOR
# ─────────────────────────────────────────────────────────────────────────────

def district_keyboard(prefix: str = "dist") -> InlineKeyboardMarkup:
    """
    prefix differentiates:
      'dist'  → registration
      'sdist' → search
      'edist' → emergency
    """
    builder = InlineKeyboardBuilder()
    for d in KERALA_DISTRICTS:
        builder.button(text=f"📍 {d}", callback_data=f"{prefix}:{d}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# DONOR RESULT CARD BUTTONS
# ─────────────────────────────────────────────────────────────────────────────

def donor_action_keyboard(phone: str, username: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    clean_phone = phone.replace(" ", "").replace("-", "")
    builder.row(
        InlineKeyboardButton(text="📞 Call Donor",      url=f"tel:{clean_phone}"),
        InlineKeyboardButton(text="💬 WhatsApp",         url=f"https://wa.me/{clean_phone}"),
    )
    if username:
        builder.row(InlineKeyboardButton(text="✈️ Telegram Chat", url=f"https://t.me/{username}"))
    builder.row(InlineKeyboardButton(text="🔍 Search Again", callback_data="find_blood"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu",    callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH PAGINATION
# ─────────────────────────────────────────────────────────────────────────────

def pagination_keyboard(
    blood_group: str,
    district: str,
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if current_page > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️ Prev",
            callback_data=f"page:{blood_group}:{district}:{current_page - 1}",
        ))
    nav.append(InlineKeyboardButton(
        text=f"📄 {current_page + 1}/{total_pages}",
        callback_data="noop",
    ))
    if current_page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            text="Next ➡️",
            callback_data=f"page:{blood_group}:{district}:{current_page + 1}",
        ))
    builder.row(*nav)
    builder.row(
        InlineKeyboardButton(text="🔍 New Search", callback_data="find_blood"),
        InlineKeyboardButton(text="🏠 Home",       callback_data="main_menu"),
    )
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# URGENCY SELECTOR (Emergency)
# ─────────────────────────────────────────────────────────────────────────────

def urgency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level in URGENCY_LEVELS:
        builder.button(text=level, callback_data=f"urgency:{level}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE EDIT MENU
# ─────────────────────────────────────────────────────────────────────────────

def profile_edit_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Name",           callback_data="edit:name"))
    builder.row(InlineKeyboardButton(text="📱 Phone",           callback_data="edit:phone"))
    builder.row(InlineKeyboardButton(text="🩸 Blood Group",     callback_data="edit:blood_group"))
    builder.row(InlineKeyboardButton(text="📍 District",        callback_data="edit:district"))
    builder.row(InlineKeyboardButton(text="🏘️ Area",            callback_data="edit:area"))
    builder.row(InlineKeyboardButton(text="🗓️ Last Donation",   callback_data="edit:last_donation"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu",       callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# AVAILABILITY TOGGLE CONFIRM
# ─────────────────────────────────────────────────────────────────────────────

def availability_keyboard(current: bool) -> InlineKeyboardMarkup:
    label = "🔴 Set as Unavailable" if current else "🟢 Set as Available"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=label, callback_data="toggle_availability"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# SKIP / CANCEL helpers
# ─────────────────────────────────────────────────────────────────────────────

def skip_keyboard(skip_callback: str = "skip") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭️ Skip", callback_data=skip_callback),
        InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu"),
    )
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────────────────────────────────────

def admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Stats",              callback_data="admin:stats"))
    builder.row(InlineKeyboardButton(text="📢 Broadcast",          callback_data="admin:broadcast"))
    builder.row(InlineKeyboardButton(text="🚨 Active Emergencies", callback_data="admin:emergencies"))
    builder.row(InlineKeyboardButton(text="📋 Export Donors",      callback_data="admin:export"))
    builder.row(InlineKeyboardButton(text="🗑️ Remove User",        callback_data="admin:remove_user"))
    builder.row(InlineKeyboardButton(text="🗑️ Clear Old Requests", callback_data="admin:clear_old"))
    builder.row(InlineKeyboardButton(text="🏠 Main Menu",          callback_data="main_menu"))
    return builder.as_markup()


# ─────────────────────────────────────────────────────────────────────────────
# BACK TO ADMIN
# ─────────────────────────────────────────────────────────────────────────────

def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="admin:panel"))
    return builder.as_markup()

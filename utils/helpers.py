"""
utils/helpers.py — Formatting helpers and rate-limiter for Kerala Blood Connect Bot
"""

import time
from collections import defaultdict
from config import config

# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────────────────────────────────────

_last_action: dict[int, float] = defaultdict(float)


def is_rate_limited(user_id: int) -> bool:
    """Return True if user has acted too recently (spam protection)."""
    now = time.monotonic()
    if now - _last_action[user_id] < config.RATE_LIMIT_SECONDS:
        return True
    _last_action[user_id] = now
    return False


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE FORMATTERS
# ─────────────────────────────────────────────────────────────────────────────

def format_donor_card(donor: dict, index: int = 1) -> str:
    """Format a single donor dict into a readable message block."""
    name = donor.get("full_name", "N/A")
    bg   = donor.get("blood_group", "N/A")
    dist = donor.get("district", "N/A")
    area = donor.get("area", "N/A")
    ph   = donor.get("phone", "N/A")
    ld   = donor.get("last_donation") or "Not provided"

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🩸 *Donor #{index}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:*         {name}\n"
        f"🩸 *Blood Group:*  {bg}\n"
        f"📍 *District:*    {dist}\n"
        f"🏘️ *Area:*         {area}\n"
        f"📞 *Phone:*        `{ph}`\n"
        f"🗓️ *Last Donated:* {ld}\n"
    )


def format_profile(user: dict) -> str:
    """Format user profile into a readable message."""
    name   = user.get("full_name", "N/A")
    bg     = user.get("blood_group", "N/A")
    dist   = user.get("district", "N/A")
    area   = user.get("area", "N/A")
    ph     = user.get("phone", "N/A")
    ld     = user.get("last_donation") or "Not provided"
    avail  = "🟢 Available" if user.get("available", True) else "🔴 Unavailable"
    reg    = user.get("registered_date")
    reg_str = reg.strftime("%d %b %Y") if reg else "N/A"

    return (
        f"╔══════════════════════╗\n"
        f"     👤 *YOUR PROFILE*\n"
        f"╚══════════════════════╝\n\n"
        f"🔖 *Name:*          {name}\n"
        f"🩸 *Blood Group:*   {bg}\n"
        f"📍 *District:*     {dist}\n"
        f"🏘️ *Area:*          {area}\n"
        f"📞 *Phone:*         `{ph}`\n"
        f"🗓️ *Last Donated:*  {ld}\n"
        f"✅ *Status:*        {avail}\n"
        f"📅 *Registered:*   {reg_str}\n"
    )


def format_emergency(req: dict) -> str:
    """Format an emergency request for broadcasting."""
    return (
        f"🚨 *EMERGENCY BLOOD REQUEST* 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Patient:*   {req.get('patient_name', 'N/A')}\n"
        f"🩸 *Blood:*     *{req.get('blood_group', 'N/A')}*\n"
        f"🏥 *Hospital:*  {req.get('hospital', 'N/A')}\n"
        f"📍 *District:*  {req.get('district', 'N/A')}\n"
        f"⚠️ *Urgency:*   {req.get('urgency', 'N/A')}\n"
        f"📞 *Contact:*   `{req.get('contact', 'N/A')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Please respond immediately if you can donate!\n"
        f"Forward this to save a life 🙏"
    )


def share_message(bot_username: str) -> str:
    return (
        f"🩸 *Kerala Blood Connect Bot*\n\n"
        f"Find verified blood donors quickly across all Kerala districts.\n\n"
        f"✅ Free & Instant\n"
        f"✅ All Blood Groups\n"
        f"✅ All 14 Kerala Districts\n"
        f"✅ Emergency Alerts\n\n"
        f"Join now 👇\n"
        f"https://t.me/{bot_username}"
    )


def help_message() -> str:
    return (
        f"❓ *HELP — Kerala Blood Connect Bot*\n\n"
        f"*Commands:*\n"
        f"• /start — Main menu\n"
        f"• /register — Become a donor\n"
        f"• /find — Search for donors\n"
        f"• /emergency — Post emergency request\n"
        f"• /profile — View your profile\n"
        f"• /availability — Toggle donor status\n"
        f"• /help — This help message\n\n"
        f"*How to donate blood?*\n"
        f"1️⃣ Register as a donor\n"
        f"2️⃣ Keep your status as Available\n"
        f"3️⃣ Respond to emergency alerts\n"
        f"4️⃣ Update last donation date after donating\n\n"
        f"🩸 You can donate every 90 days.\n\n"
        f"*Support:* Contact the admin for issues.\n"
        f"Thank you for saving lives! 🙏"
    )


def welcome_message(first_name: str) -> str:
    return (
        f"🩸 *Welcome to Kerala Blood Connect!*\n\n"
        f"Hello, *{first_name}*! 👋\n\n"
        f"We connect blood donors with people in need across all 14 Kerala districts.\n\n"
        f"📌 *What you can do:*\n"
        f"• 🩸 Register as a donor\n"
        f"• 🔍 Find donors by blood group & district\n"
        f"• 🚨 Post emergency blood requests\n"
        f"• 🔔 Get notified for matching requests\n\n"
        f"Every drop counts. Choose an option below 👇"
    )

"""
handlers/admin.py — Admin-only commands and dashboard
Access restricted to telegram IDs listed in config.ADMIN_IDS
"""

import csv
import io
import logging
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from config import config
from database import db
from keyboards import admin_keyboard, back_to_admin_keyboard, cancel_keyboard
from states import AdminStates
from utils.broadcast import broadcast_message
from utils.helpers import format_emergency

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN GUARD
# ─────────────────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def _deny(target) -> None:
    text = "⛔ You are not authorised to use admin commands."
    if isinstance(target, CallbackQuery):
        await target.answer(text, show_alert=True)
    else:
        await target.answer(text)


# ─────────────────────────────────────────────────────────────────────────────
# /admin COMMAND
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await _deny(message)
        return
    await state.clear()
    await message.answer(
        "🛡️ *ADMIN PANEL*\n\nWelcome, Administrator. Choose an action:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )


@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return
    await state.clear()
    await callback.message.edit_text(
        "🛡️ *ADMIN PANEL*\n\nWelcome, Administrator. Choose an action:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return

    total = await db.total_users()
    available = await db.total_available_donors()
    dist_stats = await db.district_stats()
    bg_stats = await db.blood_group_stats()

    dist_lines = "\n".join(
        f"  📍 {s['_id']}: {s['total']} total, {s['available']} available"
        for s in dist_stats
    ) or "  No data"

    bg_lines = "\n".join(
        f"  🩸 {s['_id']}: {s['total']}"
        for s in bg_stats
    ) or "  No data"

    text = (
        f"📊 *BOT STATISTICS*\n\n"
        f"👥 Total Registered Users: *{total}*\n"
        f"🟢 Available Donors: *{available}*\n"
        f"🔴 Unavailable: *{total - available}*\n\n"
        f"📍 *District-wise Breakdown:*\n{dist_lines}\n\n"
        f"🩸 *Blood Group Breakdown:*\n{bg_lines}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_to_admin_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVE EMERGENCIES
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:emergencies")
async def cb_emergencies(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return

    requests = await db.get_active_emergencies()
    if not requests:
        await callback.message.edit_text(
            "✅ No active emergency requests.",
            reply_markup=back_to_admin_keyboard(),
        )
        await callback.answer()
        return

    lines = []
    for r in requests[:10]:   # show max 10 to stay within message limit
        created = r.get("created_at")
        age = ""
        if created:
            delta = datetime.now(timezone.utc) - created
            age = f" ({int(delta.total_seconds() // 3600)}h ago)"
        lines.append(
            f"• {r.get('patient_name')} — {r.get('blood_group')} "
            f"@ {r.get('hospital')}, {r.get('district')}{age}"
        )

    text = f"🚨 *ACTIVE EMERGENCIES* ({len(requests)} total)\n\n" + "\n".join(lines)
    await callback.message.edit_text(
        text, parse_mode="Markdown", reply_markup=back_to_admin_keyboard()
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT DONORS (CSV)
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:export")
async def cb_export(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return

    await callback.answer("⏳ Generating CSV…")
    donors = await db.export_donors()

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["full_name", "phone", "blood_group", "district", "area", "last_donation"],
    )
    writer.writeheader()
    for d in donors:
        writer.writerow({
            "full_name": d.get("full_name", ""),
            "phone": d.get("phone", ""),
            "blood_group": d.get("blood_group", ""),
            "district": d.get("district", ""),
            "area": d.get("area", ""),
            "last_donation": d.get("last_donation", ""),
        })

    csv_bytes = buf.getvalue().encode("utf-8")
    file = BufferedInputFile(csv_bytes, filename="kerala_blood_donors.csv")

    await callback.message.answer_document(
        file,
        caption=f"📋 *Donor Export*\n{len(donors)} available donors\nGenerated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        parse_mode="Markdown",
    )
    await callback.message.edit_reply_markup(reply_markup=back_to_admin_keyboard())


# ─────────────────────────────────────────────────────────────────────────────
# BROADCAST
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return

    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.message.edit_text(
        "📢 *BROADCAST MESSAGE*\n\nType the message you want to send to ALL registered users.\n\n"
        "Supports Markdown formatting.\n"
        "Tap *Cancel* to abort.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    await state.clear()
    user_ids = await db.all_users_ids()

    status_msg = await message.answer(
        f"⏳ Broadcasting to {len(user_ids)} users… This may take a while."
    )

    result = await broadcast_message(message.bot, user_ids, message.text)

    await status_msg.edit_text(
        f"✅ *Broadcast Complete*\n\n"
        f"📨 Sent:    {result.sent}\n"
        f"🚫 Blocked: {result.blocked}\n"
        f"❌ Failed:  {result.failed}",
        parse_mode="Markdown",
        reply_markup=back_to_admin_keyboard(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# REMOVE USER
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:remove_user")
async def cb_remove_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return

    await state.set_state(AdminStates.waiting_remove_user_id)
    await callback.message.edit_text(
        "🗑️ *REMOVE USER*\n\nSend the *Telegram User ID* of the user to remove.\n\n"
        "You can get this from the user's profile or from bot logs.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_remove_user_id)
async def admin_remove_user(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    text = message.text.strip()
    if not text.lstrip("-").isdigit():
        await message.answer("❌ Invalid Telegram ID. Must be a number.", reply_markup=cancel_keyboard())
        return

    uid = int(text)
    removed = await db.remove_user(uid)
    await state.clear()

    if removed:
        await message.answer(
            f"✅ User `{uid}` has been removed from the database.",
            parse_mode="Markdown",
            reply_markup=back_to_admin_keyboard(),
        )
    else:
        await message.answer(
            f"⚠️ User `{uid}` not found in the database.",
            parse_mode="Markdown",
            reply_markup=back_to_admin_keyboard(),
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLEAR OLD EMERGENCY REQUESTS
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:clear_old")
async def cb_clear_old(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await _deny(callback)
        return

    deleted = await db.delete_old_emergencies()
    await callback.message.edit_text(
        f"🗑️ Cleared *{deleted}* expired emergency request(s).",
        parse_mode="Markdown",
        reply_markup=back_to_admin_keyboard(),
    )
    await callback.answer(f"Cleared {deleted} requests")

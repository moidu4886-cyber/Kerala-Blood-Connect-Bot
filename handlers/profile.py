"""
handlers/profile.py — View, update, and toggle availability for donors
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import (
    main_menu_keyboard,
    profile_edit_keyboard,
    availability_keyboard,
    blood_group_keyboard,
    district_keyboard,
    cancel_keyboard,
)
from states import ProfileUpdateStates
from utils.helpers import format_profile
from utils.validators import (
    validate_name,
    validate_phone,
    validate_area,
    validate_date,
    normalise_phone,
)

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW PROFILE
# ─────────────────────────────────────────────────────────────────────────────

async def _show_profile(target, user_id: int) -> None:
    user = await db.get_user(user_id)
    if not user:
        text = (
            "⚠️ *You are not registered yet.*\n\n"
            "Please register first to view your profile."
        )
    else:
        text = format_profile(user)

    markup = main_menu_keyboard()

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, parse_mode="Markdown", reply_markup=markup)


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await _show_profile(message, message.from_user.id)


@router.callback_query(F.data == "my_profile")
async def cb_profile(callback: CallbackQuery) -> None:
    await _show_profile(callback, callback.from_user.id)


# ─────────────────────────────────────────────────────────────────────────────
# TOGGLE AVAILABILITY
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("availability"))
async def cmd_availability(message: Message) -> None:
    await _handle_toggle(message, message.from_user.id, is_callback=False)


@router.callback_query(F.data == "toggle_availability")
async def cb_toggle(callback: CallbackQuery) -> None:
    await _handle_toggle(callback, callback.from_user.id, is_callback=True)


async def _handle_toggle(target, user_id: int, is_callback: bool) -> None:
    user = await db.get_user(user_id)
    if not user:
        text = "⚠️ You are not registered. Please register first."
        if is_callback:
            await target.message.edit_text(text, reply_markup=main_menu_keyboard())
            await target.answer()
        else:
            await target.answer(text, reply_markup=main_menu_keyboard())
        return

    new_status = await db.toggle_availability(user_id)
    status_text = "🟢 *Available*" if new_status else "🔴 *Unavailable*"
    text = (
        f"✅ Your donor status has been updated!\n\n"
        f"Current Status: {status_text}\n\n"
        f"{'You will now appear in donor searches.' if new_status else 'You will NOT appear in donor searches.'}"
    )

    if is_callback:
        await target.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=availability_keyboard(new_status),
        )
        await target.answer("Status updated!")
    else:
        await target.answer(text, parse_mode="Markdown",
                            reply_markup=availability_keyboard(new_status))


# ─────────────────────────────────────────────────────────────────────────────
# EDIT PROFILE — Choose field
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit_profile")
async def cb_edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "⚠️ You are not registered yet. Please register first.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await state.set_state(ProfileUpdateStates.choose_field)
    await callback.message.edit_text(
        "✏️ *EDIT PROFILE*\n\nSelect the field you want to update:",
        parse_mode="Markdown",
        reply_markup=profile_edit_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# HANDLE FIELD SELECTION
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(ProfileUpdateStates.choose_field, F.data.startswith("edit:"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]

    if field == "name":
        await state.set_state(ProfileUpdateStates.waiting_new_name)
        await callback.message.edit_text(
            "✏️ Enter your *new full name*:", parse_mode="Markdown",
            reply_markup=cancel_keyboard())

    elif field == "phone":
        await state.set_state(ProfileUpdateStates.waiting_new_phone)
        await callback.message.edit_text(
            "📱 Enter your *new phone number*:", parse_mode="Markdown",
            reply_markup=cancel_keyboard())

    elif field == "blood_group":
        await state.set_state(ProfileUpdateStates.choose_field)
        await state.update_data(editing_field="blood_group")
        await callback.message.edit_text(
            "🩸 Select your *new blood group*:", parse_mode="Markdown",
            reply_markup=blood_group_keyboard("ebg"))

    elif field == "district":
        await state.update_data(editing_field="district")
        await callback.message.edit_text(
            "📍 Select your *new district*:", parse_mode="Markdown",
            reply_markup=district_keyboard("edist"))

    elif field == "area":
        await state.set_state(ProfileUpdateStates.waiting_new_area)
        await callback.message.edit_text(
            "🏘️ Enter your *new area / town*:", parse_mode="Markdown",
            reply_markup=cancel_keyboard())

    elif field == "last_donation":
        await state.set_state(ProfileUpdateStates.waiting_new_last_donation)
        await callback.message.edit_text(
            "🗓️ Enter your *last donation date*:\nFormat: DD/MM/YYYY",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard())

    await callback.answer()


# Blood group chosen during profile edit (reuses ebg: prefix)
@router.callback_query(ProfileUpdateStates.choose_field, F.data.startswith("ebg:"))
async def edit_blood_group(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("editing_field") != "blood_group":
        await callback.answer()
        return
    bg = callback.data.split(":")[1]
    await db.update_user(callback.from_user.id, {"blood_group": bg})
    await state.clear()
    await callback.message.edit_text(
        f"✅ Blood group updated to *{bg}*!", parse_mode="Markdown",
        reply_markup=main_menu_keyboard())
    await callback.answer()


# District chosen during profile edit (reuses edist: prefix)
@router.callback_query(ProfileUpdateStates.choose_field, F.data.startswith("edist:"))
async def edit_district(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":")[1]
    await db.update_user(callback.from_user.id, {"district": district})
    await state.clear()
    await callback.message.edit_text(
        f"✅ District updated to *{district}*!", parse_mode="Markdown",
        reply_markup=main_menu_keyboard())
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# TEXT INPUT HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

@router.message(ProfileUpdateStates.waiting_new_name)
async def update_name(message: Message, state: FSMContext) -> None:
    ok, err = validate_name(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await db.update_user(message.from_user.id, {"full_name": message.text.strip()})
    await state.clear()
    await message.answer("✅ Name updated successfully!", reply_markup=main_menu_keyboard())


@router.message(ProfileUpdateStates.waiting_new_phone)
async def update_phone(message: Message, state: FSMContext) -> None:
    ok, err = validate_phone(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await db.update_user(message.from_user.id, {"phone": normalise_phone(message.text)})
    await state.clear()
    await message.answer("✅ Phone number updated!", reply_markup=main_menu_keyboard())


@router.message(ProfileUpdateStates.waiting_new_area)
async def update_area(message: Message, state: FSMContext) -> None:
    ok, err = validate_area(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await db.update_user(message.from_user.id, {"area": message.text.strip()})
    await state.clear()
    await message.answer("✅ Area updated!", reply_markup=main_menu_keyboard())


@router.message(ProfileUpdateStates.waiting_new_last_donation)
async def update_last_donation(message: Message, state: FSMContext) -> None:
    ok, result = validate_date(message.text)
    if not ok:
        await message.answer(result, reply_markup=cancel_keyboard())
        return
    await db.set_last_donation(message.from_user.id, result)
    await state.clear()
    await message.answer(
        f"✅ Last donation date updated to *{result}*!",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

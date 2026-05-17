"""
handlers/register.py — Step-by-step donor registration using FSM
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import (
    blood_group_keyboard,
    district_keyboard,
    skip_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
)
from states import RegisterStates
from utils.validators import (
    validate_name,
    validate_phone,
    validate_blood_group,
    validate_district,
    validate_area,
    validate_date,
    normalise_phone,
)

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def _start_registration(target, state: FSMContext) -> None:
    """Shared helper — works for both Message and CallbackQuery."""
    await state.set_state(RegisterStates.waiting_name)
    text = (
        "📝 *DONOR REGISTRATION*\n\n"
        "Let's register you as a blood donor! 🩸\n\n"
        "*Step 1 of 6* — Enter your *Full Name*:\n\n"
        "_Example: Rahul Menon_"
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown",
                                       reply_markup=cancel_keyboard())
        await target.answer()
    else:
        await target.answer(text, parse_mode="Markdown",
                            reply_markup=cancel_keyboard())


@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _start_registration(message, state)


@router.callback_query(F.data == "register")
async def cb_register(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _start_registration(callback, state)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Name
# ─────────────────────────────────────────────────────────────────────────────

@router.message(RegisterStates.waiting_name)
async def step_name(message: Message, state: FSMContext) -> None:
    ok, err = validate_name(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(RegisterStates.waiting_phone)
    await message.answer(
        "✅ Great!\n\n*Step 2 of 6* — Enter your *Phone Number*:\n\n"
        "_Example: 9876543210_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Phone
# ─────────────────────────────────────────────────────────────────────────────

@router.message(RegisterStates.waiting_phone)
async def step_phone(message: Message, state: FSMContext) -> None:
    ok, err = validate_phone(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await state.update_data(phone=normalise_phone(message.text))
    await state.set_state(RegisterStates.waiting_blood_group)
    await message.answer(
        "✅ Got it!\n\n*Step 3 of 6* — Select your *Blood Group*:",
        parse_mode="Markdown",
        reply_markup=blood_group_keyboard(prefix="bg"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Blood Group (inline button)
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(RegisterStates.waiting_blood_group, F.data.startswith("bg:"))
async def step_blood_group(callback: CallbackQuery, state: FSMContext) -> None:
    bg = callback.data.split(":")[1]
    ok, err = validate_blood_group(bg)
    if not ok:
        await callback.answer(err, show_alert=True)
        return
    await state.update_data(blood_group=bg)
    await state.set_state(RegisterStates.waiting_district)
    await callback.message.edit_text(
        f"✅ Blood group *{bg}* selected!\n\n*Step 4 of 6* — Select your *District*:",
        parse_mode="Markdown",
        reply_markup=district_keyboard(prefix="dist"),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — District (inline button)
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(RegisterStates.waiting_district, F.data.startswith("dist:"))
async def step_district(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":")[1]
    ok, err = validate_district(district)
    if not ok:
        await callback.answer(err, show_alert=True)
        return
    await state.update_data(district=district)
    await state.set_state(RegisterStates.waiting_area)
    await callback.message.edit_text(
        f"✅ District *{district}* selected!\n\n"
        f"*Step 5 of 6* — Enter your *Area / Town / Panchayat*:\n\n"
        f"_Example: Kazhakkoottam_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Area
# ─────────────────────────────────────────────────────────────────────────────

@router.message(RegisterStates.waiting_area)
async def step_area(message: Message, state: FSMContext) -> None:
    ok, err = validate_area(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await state.update_data(area=message.text.strip())
    await state.set_state(RegisterStates.waiting_last_donation)
    await message.answer(
        "✅ Almost done!\n\n"
        "*Step 6 of 6* — Enter your *Last Donation Date* _(optional)_:\n\n"
        "Format: DD/MM/YYYY  e.g. `25/12/2023`\n"
        "Tap *Skip* if you have never donated before.",
        parse_mode="Markdown",
        reply_markup=skip_keyboard(skip_callback="skip_donation_date"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Last Donation Date (optional)
# ─────────────────────────────────────────────────────────────────────────────

@router.message(RegisterStates.waiting_last_donation)
async def step_last_donation(message: Message, state: FSMContext) -> None:
    ok, result = validate_date(message.text)
    if not ok:
        await message.answer(result, reply_markup=skip_keyboard(skip_callback="skip_donation_date"))
        return
    await state.update_data(last_donation=result)
    await _finish_registration(message, state)


@router.callback_query(F.data == "skip_donation_date")
async def skip_donation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(last_donation=None)
    await _finish_registration(callback.message, state, from_callback=True)
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# FINISH
# ─────────────────────────────────────────────────────────────────────────────

async def _finish_registration(
    message: Message,
    state: FSMContext,
    from_callback: bool = False,
) -> None:
    data = await state.get_data()
    user_id = message.chat.id

    # Build user document
    user_doc = {
        "telegram_id": user_id,
        "username": None,   # will be refreshed on next /start
        "full_name": data["full_name"],
        "phone": data["phone"],
        "blood_group": data["blood_group"],
        "district": data["district"],
        "area": data["area"],
        "last_donation": data.get("last_donation"),
    }

    await db.register_user(user_doc)
    await state.clear()

    summary = (
        "🎉 *Registration Successful!*\n\n"
        "You are now a registered blood donor in Kerala Blood Connect.\n\n"
        f"🔖 *Name:*         {data['full_name']}\n"
        f"🩸 *Blood Group:*  {data['blood_group']}\n"
        f"📍 *District:*    {data['district']}\n"
        f"🏘️ *Area:*         {data['area']}\n"
        f"📞 *Phone:*        {data['phone']}\n"
        f"🗓️ *Last Donated:* {data.get('last_donation') or 'Not provided'}\n\n"
        "✅ Your status is set to *Available*.\n"
        "You will receive emergency alerts matching your blood group & district.\n\n"
        "Thank you for saving lives! 🙏"
    )

    send_fn = message.edit_text if from_callback else message.answer
    await send_fn(summary, parse_mode="Markdown", reply_markup=main_menu_keyboard())

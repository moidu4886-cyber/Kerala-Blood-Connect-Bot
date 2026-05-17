"""
handlers/emergency.py — Emergency blood request submission & broadcasting
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
    urgency_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
)
from states import EmergencyStates
from utils.broadcast import broadcast_to_matching_donors
from utils.helpers import format_emergency
from utils.validators import validate_name, validate_phone, normalise_phone

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def _start_emergency(target, state: FSMContext) -> None:
    await state.set_state(EmergencyStates.waiting_patient_name)
    text = (
        "🚨 *EMERGENCY BLOOD REQUEST*\n\n"
        "Fill in the details below. Your request will be sent to matching donors immediately.\n\n"
        "*Step 1 of 6* — Enter the *Patient's Name*:"
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown",
                                       reply_markup=cancel_keyboard())
        await target.answer()
    else:
        await target.answer(text, parse_mode="Markdown", reply_markup=cancel_keyboard())


@router.message(Command("emergency"))
async def cmd_emergency(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _start_emergency(message, state)


@router.callback_query(F.data == "emergency")
async def cb_emergency(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _start_emergency(callback, state)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Patient Name
# ─────────────────────────────────────────────────────────────────────────────

@router.message(EmergencyStates.waiting_patient_name)
async def em_patient_name(message: Message, state: FSMContext) -> None:
    ok, err = validate_name(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await state.update_data(patient_name=message.text.strip())
    await state.set_state(EmergencyStates.waiting_blood_group)
    await message.answer(
        "*Step 2 of 6* — Select the *Blood Group* required:",
        parse_mode="Markdown",
        reply_markup=blood_group_keyboard("ebg"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Blood Group
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(EmergencyStates.waiting_blood_group, F.data.startswith("ebg:"))
async def em_blood_group(callback: CallbackQuery, state: FSMContext) -> None:
    bg = callback.data.split(":")[1]
    await state.update_data(blood_group=bg)
    await state.set_state(EmergencyStates.waiting_district)
    await callback.message.edit_text(
        f"🩸 Blood group *{bg}* selected!\n\n*Step 3 of 6* — Select *District* (hospital location):",
        parse_mode="Markdown",
        reply_markup=district_keyboard("edist"),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — District
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(EmergencyStates.waiting_district, F.data.startswith("edist:"))
async def em_district(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":")[1]
    await state.update_data(district=district)
    await state.set_state(EmergencyStates.waiting_hospital)
    await callback.message.edit_text(
        f"📍 District *{district}* selected!\n\n*Step 4 of 6* — Enter the *Hospital Name*:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Hospital
# ─────────────────────────────────────────────────────────────────────────────

@router.message(EmergencyStates.waiting_hospital)
async def em_hospital(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if len(text) < 3:
        await message.answer("❌ Hospital name too short.", reply_markup=cancel_keyboard())
        return
    await state.update_data(hospital=text)
    await state.set_state(EmergencyStates.waiting_contact)
    await message.answer(
        "*Step 5 of 6* — Enter the *Contact Number* for this emergency:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Contact
# ─────────────────────────────────────────────────────────────────────────────

@router.message(EmergencyStates.waiting_contact)
async def em_contact(message: Message, state: FSMContext) -> None:
    ok, err = validate_phone(message.text)
    if not ok:
        await message.answer(err, reply_markup=cancel_keyboard())
        return
    await state.update_data(contact=normalise_phone(message.text))
    await state.set_state(EmergencyStates.waiting_urgency)
    await message.answer(
        "*Step 6 of 6* — Select the *Urgency Level*:",
        parse_mode="Markdown",
        reply_markup=urgency_keyboard(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Urgency → Submit
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(EmergencyStates.waiting_urgency, F.data.startswith("urgency:"))
async def em_urgency(callback: CallbackQuery, state: FSMContext) -> None:
    urgency = callback.data.split(":", 1)[1]
    data = await state.get_data()
    data["urgency"] = urgency
    data["requester_id"] = callback.from_user.id

    # Save to DB
    req_id = await db.save_emergency(data)
    await state.clear()

    # Format broadcast text
    broadcast_text = format_emergency(data)

    # Confirm to requester first
    await callback.message.edit_text(
        f"✅ *Emergency request submitted!*\n\n"
        f"{broadcast_text}\n\n"
        f"🔔 Notifying matching donors in *{data['district']}*…",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer("Request submitted!")

    # Async broadcast to matching donors
    result = await broadcast_to_matching_donors(
        callback.bot,
        data["blood_group"],
        data["district"],
        broadcast_text,
    )

    # Follow-up count message
    count_msg = (
        f"\n✅ Notified *{result.sent}* donor(s) in {data['district']} "
        f"for blood group {data['blood_group']}."
    )
    try:
        await callback.message.answer(count_msg, parse_mode="Markdown")
    except Exception:
        pass

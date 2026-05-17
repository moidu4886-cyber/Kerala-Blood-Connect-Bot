"""
handlers/search.py — Find blood donor flow with pagination
"""

import logging
import math

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import config
from database import db
from keyboards import (
    blood_group_keyboard,
    district_keyboard,
    donor_action_keyboard,
    pagination_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
)
from states import SearchStates
from utils.helpers import format_donor_card

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def _start_search(target, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_blood_group)
    text = "🔍 *FIND BLOOD DONOR*\n\n*Step 1 of 2* — Select *Blood Group* needed:"
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="Markdown",
                                       reply_markup=blood_group_keyboard("sbg"))
        await target.answer()
    else:
        await target.answer(text, parse_mode="Markdown",
                            reply_markup=blood_group_keyboard("sbg"))


@router.message(Command("find"))
async def cmd_find(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _start_search(message, state)


@router.callback_query(F.data == "find_blood")
async def cb_find(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _start_search(callback, state)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Blood Group
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(SearchStates.waiting_blood_group, F.data.startswith("sbg:"))
async def search_blood_group(callback: CallbackQuery, state: FSMContext) -> None:
    bg = callback.data.split(":")[1]
    await state.update_data(blood_group=bg)
    await state.set_state(SearchStates.waiting_district)
    await callback.message.edit_text(
        f"🩸 Blood group *{bg}* selected!\n\n*Step 2 of 2* — Select *District*:",
        parse_mode="Markdown",
        reply_markup=district_keyboard("sdist"),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — District → Show results (page 0)
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(SearchStates.waiting_district, F.data.startswith("sdist:"))
async def search_district(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":")[1]
    data = await state.get_data()
    blood_group = data["blood_group"]

    await state.update_data(district=district)
    await state.set_state(SearchStates.viewing_results)

    await _show_results_page(callback, blood_group, district, page=0)


# ─────────────────────────────────────────────────────────────────────────────
# PAGINATION
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("page:"))
async def paginate(callback: CallbackQuery, state: FSMContext) -> None:
    # page:<blood_group>:<district>:<page_number>
    parts = callback.data.split(":")
    blood_group = parts[1]
    district = parts[2]
    page = int(parts[3])
    await _show_results_page(callback, blood_group, district, page)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED RESULT RENDERER
# ─────────────────────────────────────────────────────────────────────────────

async def _show_results_page(
    callback: CallbackQuery,
    blood_group: str,
    district: str,
    page: int,
) -> None:
    per_page = config.MAX_DONORS_PER_PAGE
    total = await db.count_donors(blood_group, district)

    if total == 0:
        await callback.message.edit_text(
            f"😔 *No donors found*\n\n"
            f"Blood Group: *{blood_group}*\n"
            f"District: *{district}*\n\n"
            f"No available donors match your criteria right now.\n"
            f"Please try again later or post an *Emergency Request*.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    total_pages = math.ceil(total / per_page)
    page = max(0, min(page, total_pages - 1))
    skip = page * per_page

    donors = await db.find_donors(blood_group, district, skip=skip, limit=per_page)

    header = (
        f"🩸 *DONORS FOUND* — {blood_group} in {district}\n"
        f"📊 Total: {total} available donor(s)\n\n"
    )

    # Build combined message for page
    cards = []
    for i, donor in enumerate(donors):
        global_index = skip + i + 1
        cards.append(format_donor_card(donor, index=global_index))

    full_text = header + "\n".join(cards)

    # Truncate if somehow too long (Telegram 4096 char limit)
    if len(full_text) > 4000:
        full_text = full_text[:3990] + "\n…"

    # For the first donor on the page, add action buttons
    first_donor = donors[0]
    first_phone = first_donor.get("phone", "")
    first_username = first_donor.get("username")

    markup = pagination_keyboard(blood_group, district, page, total_pages)

    await callback.message.edit_text(
        full_text,
        parse_mode="Markdown",
        reply_markup=markup,
    )
    await callback.answer(f"Page {page + 1} of {total_pages}")

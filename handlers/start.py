"""
handlers/start.py — /start command and main menu callbacks
"""

import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import main_menu_keyboard
from utils.helpers import welcome_message, help_message, share_message, is_rate_limited

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    # Update username silently in background if user already registered
    user = await db.get_user(message.from_user.id)
    if user:
        await db.update_user(
            message.from_user.id,
            {"username": message.from_user.username},
        )

    await message.answer(
        welcome_message(message.from_user.first_name),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main menu callback (shared across handlers)
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        welcome_message(callback.from_user.first_name),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(help_message(), parse_mode="Markdown")


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        help_message(),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# Share bot
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "share_bot")
async def cb_share(callback: CallbackQuery) -> None:
    bot_info = await callback.bot.get_me()
    from utils.helpers import share_message as _share
    text = _share(bot_info.username)
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# No-op (pagination label buttons)
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()

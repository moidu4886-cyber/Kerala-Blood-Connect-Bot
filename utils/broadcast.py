"""
utils/broadcast.py — Async broadcast helpers for Kerala Blood Connect Bot
Sends a message to a list of Telegram user IDs with rate limiting
and returns counts of successes / failures.
"""

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import config

logger = logging.getLogger(__name__)


@dataclass
class BroadcastResult:
    sent: int = 0
    failed: int = 0
    blocked: int = 0


async def broadcast_message(
    bot: Bot,
    user_ids: list[int],
    text: str,
    parse_mode: str = "Markdown",
) -> BroadcastResult:
    """
    Send `text` to every user_id in the list.
    - Waits `config.BROADCAST_DELAY` seconds between each send to stay within Telegram limits.
    - Catches Forbidden errors (user blocked the bot) gracefully.
    """
    result = BroadcastResult()

    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode=parse_mode)
            result.sent += 1
        except TelegramForbiddenError:
            # User blocked the bot
            result.blocked += 1
        except TelegramBadRequest as e:
            logger.warning("Bad request for user %d: %s", uid, e)
            result.failed += 1
        except Exception as e:
            logger.error("Unexpected error sending to %d: %s", uid, e)
            result.failed += 1

        await asyncio.sleep(config.BROADCAST_DELAY)

    logger.info(
        "Broadcast complete — sent: %d, blocked: %d, failed: %d",
        result.sent, result.blocked, result.failed,
    )
    return result


async def broadcast_to_matching_donors(
    bot: Bot,
    blood_group: str,
    district: str,
    text: str,
) -> BroadcastResult:
    """
    Notify only donors matching `blood_group` and `district` who are available.
    Imported lazily to avoid circular imports.
    """
    from database import db  # local import to avoid circular dependency

    cursor = db.users.find(
        {"blood_group": blood_group, "district": district, "available": True},
        {"telegram_id": 1},
    )
    docs = await cursor.to_list(length=10_000)
    ids = [d["telegram_id"] for d in docs]

    if not ids:
        return BroadcastResult()

    return await broadcast_message(bot, ids, text)

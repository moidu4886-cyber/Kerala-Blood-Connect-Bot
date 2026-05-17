"""
bot.py — Kerala Blood Connect Bot — Main Entry Point
Initialises aiogram 3, registers all routers, connects to MongoDB, and starts polling.

Deploy on: Koyeb · Render · Railway
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import db
from handlers import start, register, search, emergency, profile, admin

# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Background tasks ──────────────────────────────────────────────────────────

async def cleanup_emergencies_task() -> None:
    """Run once every hour: delete expired emergency requests."""
    import asyncio as _asyncio
    while True:
        await _asyncio.sleep(3600)
        try:
            deleted = await db.delete_old_emergencies()
            if deleted:
                logger.info("Auto-cleanup: removed %d expired emergency request(s)", deleted)
        except Exception as e:
            logger.error("Emergency cleanup error: %s", e)


async def donation_reminder_task(bot: Bot) -> None:
    """Run once per day: remind donors who are due for donation."""
    import asyncio as _asyncio
    while True:
        await _asyncio.sleep(86400)   # 24 h
        try:
            donors = await db.donors_due_for_reminder()
            for donor in donors:
                try:
                    await bot.send_message(
                        donor["telegram_id"],
                        "🩸 *Donation Reminder*\n\n"
                        "It has been 90+ days since your last blood donation.\n"
                        "You are now eligible to donate again!\n\n"
                        "Please update your availability so people in need can find you.\n\n"
                        "Use /availability to toggle your status. Thank you! 🙏",
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass   # User may have blocked the bot
        except Exception as e:
            logger.error("Donation reminder task error: %s", e)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set in .env — exiting.")
        sys.exit(1)
    if not config.MONGO_URI:
        logger.critical("MONGO_URI is not set in .env — exiting.")
        sys.exit(1)
    if not config.ADMIN_IDS:
        logger.warning("ADMIN_ID not set — admin commands will be inaccessible.")

    # ── Connect to MongoDB ────────────────────────────────────────────────────
    await db.connect()

    # ── Bot & Dispatcher ─────────────────────────────────────────────────────
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ── Register routers (order matters: more specific → more general) ────────
    dp.include_router(admin.router)      # admin first — guard checks inside
    dp.include_router(register.router)
    dp.include_router(search.router)
    dp.include_router(emergency.router)
    dp.include_router(profile.router)
    dp.include_router(start.router)      # start last (catch-all main_menu)

    # ── Background tasks ──────────────────────────────────────────────────────
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_emergencies_task())
    loop.create_task(donation_reminder_task(bot))

    logger.info("Kerala Blood Connect Bot is starting… 🩸")

    # ── Drop accumulated updates, then start polling ──────────────────────────
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.disconnect()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())

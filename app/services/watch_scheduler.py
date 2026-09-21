import asyncio
import logging

from aiogram import Bot

from app.models.username import UsernameStatus
from app.services.instagram_checker import InstagramChecker
from app.services.watch_store import WatchStore

logger = logging.getLogger(__name__)


async def run_watch_cycle(
    bot: Bot, checker: InstagramChecker, store: WatchStore, delay_seconds: float
) -> None:
    """Checks every watched username once and notifies + stops watching any that are AVAILABLE."""
    for entry in store.all_entries():
        status = await checker.check(entry.username)
        if status == UsernameStatus.AVAILABLE:
            store.remove_by_id(entry.id)
            try:
                await bot.send_message(
                    entry.user_id,
                    f"🎉 @{entry.username} looks AVAILABLE now!\n\n"
                    "I've stopped watching it — grab it before someone else does.",
                )
            except Exception:
                logger.exception("Failed to notify user %s about @%s", entry.user_id, entry.username)
        await asyncio.sleep(delay_seconds)


async def watch_loop(
    bot: Bot,
    checker: InstagramChecker,
    store: WatchStore,
    interval_seconds: float,
    delay_seconds: float,
) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await run_watch_cycle(bot, checker, store, delay_seconds)
        except Exception:
            logger.exception("Watch cycle failed")

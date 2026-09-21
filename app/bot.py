import asyncio
import logging
import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, ErrorEvent

from app.config import Config
from app.handlers import bulk, check, start, watch
from app.services.instagram_checker import HttpInstagramChecker
from app.services.watch_scheduler import watch_loop
from app.services.watch_store import WatchStore

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start", description="Welcome & instructions"),
    BotCommand(command="check", description="Check a single username"),
    BotCommand(command="bulk", description="Check multiple usernames"),
    BotCommand(command="watch", description="Watch usernames for availability"),
    BotCommand(command="watching", description="List usernames you're watching"),
    BotCommand(command="unwatch", description="Stop watching a username"),
    BotCommand(command="help", description="Show help"),
    BotCommand(command="status", description="Bot status"),
]


def create_dispatcher(config: Config) -> Dispatcher:
    checker = HttpInstagramChecker(
        timeout=config.request_timeout, max_concurrent=config.max_concurrent_checks
    )
    store = WatchStore(config.watch_db_path)
    dp = Dispatcher()
    dp["checker"] = checker
    dp["config"] = config
    dp["store"] = store
    dp["started_at"] = time.monotonic()

    dp.include_router(start.router)
    dp.include_router(check.router)
    dp.include_router(bulk.router)
    dp.include_router(watch.router)

    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        logger.exception("Unhandled error while processing update", exc_info=event.exception)
        return True

    return dp


async def run_bot(config: Config) -> None:
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher(config)
    await bot.set_my_commands(BOT_COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)

    watch_task = asyncio.create_task(
        watch_loop(
            bot,
            dp["checker"],
            dp["store"],
            config.watch_interval_seconds,
            config.bulk_delay_seconds,
        )
    )
    try:
        logger.info("Starting bot polling")
        await dp.start_polling(bot)
    finally:
        watch_task.cancel()

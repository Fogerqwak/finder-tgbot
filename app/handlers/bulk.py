import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app.handlers.check import format_result
from app.models.username import UsernameStatus
from app.services.instagram_checker import InstagramChecker
from app.states import BulkStates
from app.utils.keyboards import check_again_keyboard
from app.utils.ratelimit import RateLimiter
from app.utils.telegram import callback_message
from app.utils.validation import parse_bulk_input

logger = logging.getLogger(__name__)
router = Router(name="bulk")

_rate_limiter = RateLimiter()


def _prompt(config: Config) -> str:
    return (
        "📋 Send me the usernames to check, one per line "
        f"(up to {config.max_bulk_usernames}). With or without @."
    )


def _summarize(results: list[tuple[str, UsernameStatus]]) -> str:
    counts = {status: 0 for status in UsernameStatus}
    for _, status in results:
        counts[status] += 1
    return (
        "📊 Summary: "
        f"✅ {counts[UsernameStatus.AVAILABLE]} available, "
        f"❌ {counts[UsernameStatus.UNAVAILABLE]} unavailable, "
        f"⚠️ {counts[UsernameStatus.UNKNOWN]} unknown"
    )


@router.message(Command("bulk"))
async def cmd_bulk(message: Message, state: FSMContext, config: Config) -> None:
    await state.clear()
    await state.set_state(BulkStates.waiting_for_usernames)
    await message.answer(_prompt(config))


@router.callback_query(F.data == "bulk_new")
async def cb_bulk_new(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    await state.set_state(BulkStates.waiting_for_usernames)
    message = callback_message(callback)
    if message is not None:
        await message.answer(_prompt(config))
    await callback.answer()


@router.message(BulkStates.waiting_for_usernames, F.text)
async def receive_bulk(
    message: Message, state: FSMContext, checker: InstagramChecker, config: Config
) -> None:
    await state.clear()
    if message.from_user is None or message.text is None:
        return
    user_id = message.from_user.id

    reason = _rate_limiter.check(user_id, config.rate_limit_seconds)
    if reason == "in_flight":
        await message.answer("⏳ Still working on your previous request — please wait.")
        return
    if reason == "cooldown":
        await message.answer("🐢 You're checking too fast. Please wait a moment and try again.")
        return

    valid, invalid, truncated = parse_bulk_input(message.text, config.max_bulk_usernames)
    if not valid:
        await message.answer(
            "⚠️ I couldn't find any valid usernames in that message. "
            "Send one username per line."
        )
        return

    _rate_limiter.start(user_id)
    try:
        notes = []
        if invalid:
            notes.append(f"({len(invalid)} invalid line(s) skipped)")
        if truncated:
            notes.append("(list truncated to the limit)")
        status_message = await message.answer(
            f"🔍 Checking {len(valid)} username(s)...\n" + " ".join(notes)
        )

        results: list[tuple[str, UsernameStatus]] = []
        for username in valid:
            status = await checker.check(username)
            results.append((username, status))
            await asyncio.sleep(config.bulk_delay_seconds)

        body = "\n\n".join(format_result(u, s) for u, s in results)
        await status_message.edit_text(f"{body}\n\n{_summarize(results)}")
        await message.answer("What next?", reply_markup=check_again_keyboard())
    except Exception:
        logger.exception("Unexpected error during bulk check")
        await message.answer(
            "⚠️ Something went wrong during the bulk check. Please try again later."
        )
    finally:
        _rate_limiter.finish(user_id)

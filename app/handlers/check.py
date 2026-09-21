import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app.models.username import UsernameStatus
from app.services.instagram_checker import InstagramChecker
from app.states import CheckStates
from app.utils.keyboards import check_again_keyboard
from app.utils.ratelimit import RateLimiter
from app.utils.telegram import callback_message
from app.utils.validation import (
    extract_username_arg,
    is_valid_username,
    normalize_username,
)

logger = logging.getLogger(__name__)
router = Router(name="check")

_rate_limiter = RateLimiter()

INVALID_USERNAME_MSG = (
    "⚠️ That doesn't look like a valid Instagram username. "
    "Use 1-30 letters, numbers, periods or underscores (no leading/trailing "
    "or double periods)."
)

STATUS_TEXT = {
    UsernameStatus.AVAILABLE: ("✅", "AVAILABLE", "The username appears to be available."),
    UsernameStatus.UNAVAILABLE: ("❌", "UNAVAILABLE", "This username appears to be taken."),
    UsernameStatus.UNKNOWN: (
        "⚠️",
        "UNKNOWN",
        (
            "Instagram did not provide enough information to confirm availability. "
            "Try again later."
        ),
    ),
}


def format_result(username: str, status: UsernameStatus) -> str:
    emoji, label, detail = STATUS_TEXT[status]
    return f"👤 @{username}\n{emoji} Status: {label}\n\n{detail}"


async def run_check(
    message: Message, username: str, checker: InstagramChecker, config: Config
) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    reason = _rate_limiter.check(user_id, config.rate_limit_seconds)
    if reason == "in_flight":
        await message.answer("⏳ Still working on your previous request — please wait.")
        return
    if reason == "cooldown":
        await message.answer("🐢 You're checking too fast. Please wait a moment and try again.")
        return

    _rate_limiter.start(user_id)
    try:
        status_message = await message.answer("🔍 Checking Instagram username...")
        status = await checker.check(username)
        await status_message.edit_text(format_result(username, status))
        await message.answer("What next?", reply_markup=check_again_keyboard())
    except Exception:
        logger.exception("Unexpected error while checking %s", username)
        await message.answer(
            "⚠️ Something went wrong while checking that username. Please try again later."
        )
    finally:
        _rate_limiter.finish(user_id)


@router.message(Command("check"))
async def cmd_check(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    checker: InstagramChecker,
    config: Config,
) -> None:
    await state.clear()
    raw = extract_username_arg(command.args)
    if raw is None:
        await state.set_state(CheckStates.waiting_for_username)
        await message.answer("Send me the username you'd like to check (with or without @).")
        return

    username = normalize_username(raw)
    if not is_valid_username(username):
        await message.answer(INVALID_USERNAME_MSG)
        return

    await run_check(message, username, checker, config)


@router.message(CheckStates.waiting_for_username, F.text)
async def receive_username(
    message: Message, state: FSMContext, checker: InstagramChecker, config: Config
) -> None:
    await state.clear()
    if message.text is None:
        return
    username = normalize_username(message.text)
    if not is_valid_username(username):
        await message.answer(INVALID_USERNAME_MSG)
        return
    await run_check(message, username, checker, config)


@router.callback_query(F.data == "check_new")
async def cb_check_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CheckStates.waiting_for_username)
    message = callback_message(callback)
    if message is not None:
        await message.answer("Send me the username you'd like to check (with or without @).")
    await callback.answer()

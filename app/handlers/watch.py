import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import Config
from app.services.watch_store import WatchStore
from app.states import WatchStates
from app.utils.validation import (
    extract_username_arg,
    normalize_username,
    parse_bulk_input,
)

logger = logging.getLogger(__name__)
router = Router(name="watch")


def _prompt(remaining: int) -> str:
    return (
        "👀 Send me the usernames you want me to watch, one per line "
        f"(up to {remaining} more). I'll check them hourly and message you the "
        "moment one looks available."
    )


@router.message(Command("watch"))
async def cmd_watch(
    message: Message, state: FSMContext, store: WatchStore, config: Config
) -> None:
    await state.clear()
    if message.from_user is None:
        return
    remaining = config.max_watches_per_user - store.count_for_user(message.from_user.id)
    if remaining <= 0:
        await message.answer(
            f"You're already watching the maximum of {config.max_watches_per_user} "
            "usernames. Use /watching to see them or /unwatch <username> to free up a slot."
        )
        return
    await state.set_state(WatchStates.waiting_for_usernames)
    await message.answer(_prompt(remaining))


@router.message(WatchStates.waiting_for_usernames, F.text)
async def receive_watch_list(
    message: Message, state: FSMContext, store: WatchStore, config: Config
) -> None:
    await state.clear()
    if message.from_user is None or message.text is None:
        return
    user_id = message.from_user.id

    remaining = config.max_watches_per_user - store.count_for_user(user_id)
    if remaining <= 0:
        await message.answer("You're already watching the maximum number of usernames.")
        return

    valid, invalid, truncated = parse_bulk_input(message.text, remaining)
    if not valid:
        await message.answer("⚠️ I couldn't find any valid usernames in that message.")
        return

    added = [u for u in valid if store.add(user_id, u)]
    duplicates = [u for u in valid if u not in added]

    lines = []
    if added:
        lines.append("👀 Now watching: " + ", ".join(f"@{u}" for u in added))
    if duplicates:
        lines.append("Already watching: " + ", ".join(f"@{u}" for u in duplicates))
    if invalid:
        lines.append(f"Skipped {len(invalid)} invalid line(s).")
    if truncated:
        lines.append(f"You can only watch {config.max_watches_per_user} at a time — the rest were dropped.")
    lines.append("I'll check hourly and message you here the moment one becomes available.")
    await message.answer("\n".join(lines))


@router.message(Command("unwatch"))
async def cmd_unwatch(message: Message, command: CommandObject, store: WatchStore) -> None:
    if message.from_user is None:
        return
    raw = extract_username_arg(command.args)
    if raw is None:
        await message.answer("Usage: /unwatch <username>")
        return
    username = normalize_username(raw)
    if store.remove(message.from_user.id, username):
        await message.answer(f"🛑 Stopped watching @{username}.")
    else:
        await message.answer(f"@{username} wasn't on your watch list.")


@router.message(Command("watching"))
async def cmd_watching(message: Message, store: WatchStore, config: Config) -> None:
    if message.from_user is None:
        return
    usernames = store.list_for_user(message.from_user.id)
    if not usernames:
        await message.answer(
            "You're not watching any usernames yet. Use /watch to add up to "
            f"{config.max_watches_per_user}."
        )
        return
    listing = "\n".join(f"• @{u}" for u in usernames)
    await message.answer(f"👀 Watching {len(usernames)} username(s):\n{listing}")

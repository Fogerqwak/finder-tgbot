import time
from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app.utils.keyboards import main_menu_keyboard
from app.utils.telegram import callback_message

router = Router(name="start")

WELCOME = (
    "👋 <b>Instagram Username Checker</b>\n\n"
    "I check whether Instagram usernames appear to be available.\n\n"
    "<b>Commands</b>\n"
    "/check &lt;username&gt; — check one username right now\n"
    "/bulk — check a list of usernames right now\n"
    "/watch — watch up to 10 usernames, checked hourly\n"
    "/watching — see what you're watching\n"
    "/unwatch &lt;username&gt; — stop watching one\n"
    "/help — show help\n"
    "/status — bot status\n\n"
    "You can include or omit the @ — both work."
)

HELP = (
    "<b>How to use this bot</b>\n\n"
    "• <code>/check username123</code> — check a single username right now\n"
    "• <code>/check @username123</code> — the @ is optional\n"
    "• <code>/bulk</code> — then send one username per line to check several at once\n\n"
    "<b>Passive watching</b>\n"
    "• <code>/watch</code> — then send up to 10 usernames, one per line. "
    "I'll check them once an hour and message you the moment one looks available.\n"
    "• <code>/watching</code> — list what you're currently watching\n"
    "• <code>/unwatch username123</code> — stop watching one\n\n"
    "<b>Statuses</b>\n"
    "✅ AVAILABLE — no active profile found\n"
    "❌ UNAVAILABLE — the username is taken\n"
    "⚠️ UNKNOWN — Instagram didn't give a clear answer, try again later\n\n"
    "Results are best-effort: a username can still be reserved or restricted "
    "even if it looks available."
)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP)


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    message = callback_message(callback)
    if message is not None:
        await message.answer(HELP)
    await callback.answer()


@router.message(Command("status"))
async def cmd_status(message: Message, config: Config, started_at: float) -> None:
    uptime = timedelta(seconds=int(time.monotonic() - started_at))
    await message.answer(
        "🤖 <b>Bot status</b>\n"
        "Status: online\n"
        f"Uptime: {uptime}\n"
        "Checker backend: public profile-page lookup\n"
        f"Bulk limit: {config.max_bulk_usernames} usernames per request"
    )

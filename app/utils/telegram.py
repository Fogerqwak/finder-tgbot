from aiogram.types import CallbackQuery, Message


def callback_message(callback: CallbackQuery) -> Message | None:
    """A callback's message can be None or an InaccessibleMessage (too old to edit/reply to)."""
    return callback.message if isinstance(callback.message, Message) else None

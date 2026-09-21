from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Check a username", callback_data="check_new")],
            [InlineKeyboardButton(text="📋 Bulk check", callback_data="bulk_new")],
            [InlineKeyboardButton(text="❓ Help", callback_data="help")],
        ]
    )


def check_again_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Check another username", callback_data="check_new")],
        ]
    )

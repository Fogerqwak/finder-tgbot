from aiogram.fsm.state import State, StatesGroup


class CheckStates(StatesGroup):
    waiting_for_username = State()


class BulkStates(StatesGroup):
    waiting_for_usernames = State()


class WatchStates(StatesGroup):
    waiting_for_usernames = State()

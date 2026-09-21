from unittest.mock import AsyncMock

import pytest

from app.models.username import UsernameStatus
from app.services.watch_scheduler import run_watch_cycle
from app.services.watch_store import WatchStore


class FakeChecker:
    def __init__(self, statuses: dict[str, UsernameStatus]) -> None:
        self._statuses = statuses

    async def check(self, username: str) -> UsernameStatus:
        return self._statuses[username]


@pytest.mark.asyncio
async def test_available_username_notifies_and_stops_watching(tmp_path):
    store = WatchStore(str(tmp_path / "watch.db"))
    store.add(1, "freeuser")
    checker = FakeChecker({"freeuser": UsernameStatus.AVAILABLE})
    bot = AsyncMock()

    await run_watch_cycle(bot, checker, store, delay_seconds=0)

    bot.send_message.assert_awaited_once()
    args, _ = bot.send_message.call_args
    assert args[0] == 1
    assert "freeuser" in args[1]
    assert store.count_for_user(1) == 0


@pytest.mark.asyncio
async def test_unavailable_username_keeps_watching_without_notifying(tmp_path):
    store = WatchStore(str(tmp_path / "watch.db"))
    store.add(1, "takenuser")
    checker = FakeChecker({"takenuser": UsernameStatus.UNAVAILABLE})
    bot = AsyncMock()

    await run_watch_cycle(bot, checker, store, delay_seconds=0)

    bot.send_message.assert_not_awaited()
    assert store.count_for_user(1) == 1


@pytest.mark.asyncio
async def test_unknown_username_keeps_watching_without_notifying(tmp_path):
    store = WatchStore(str(tmp_path / "watch.db"))
    store.add(1, "mysteryuser")
    checker = FakeChecker({"mysteryuser": UsernameStatus.UNKNOWN})
    bot = AsyncMock()

    await run_watch_cycle(bot, checker, store, delay_seconds=0)

    bot.send_message.assert_not_awaited()
    assert store.count_for_user(1) == 1

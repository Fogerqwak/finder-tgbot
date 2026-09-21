import time


class RateLimiter:
    """Per-user cooldown + duplicate-in-flight-request guard.

    In-memory only: this state doesn't need to survive a restart, so no
    persistence layer is used here.
    """

    def __init__(self) -> None:
        self._last_request: dict[int, float] = {}
        self._in_flight: set[int] = set()

    def check(self, user_id: int, min_interval: float) -> str | None:
        """Returns None if allowed, else a reason: 'in_flight' or 'cooldown'."""
        if user_id in self._in_flight:
            return "in_flight"
        last = self._last_request.get(user_id, 0.0)
        if time.monotonic() - last < min_interval:
            return "cooldown"
        return None

    def start(self, user_id: int) -> None:
        self._in_flight.add(user_id)
        self._last_request[user_id] = time.monotonic()

    def finish(self, user_id: int) -> None:
        self._in_flight.discard(user_id)

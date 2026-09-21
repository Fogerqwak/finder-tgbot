import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    max_bulk_usernames: int = 20
    rate_limit_seconds: float = 3.0
    request_timeout: float = 10.0
    max_concurrent_checks: int = 2
    bulk_delay_seconds: float = 1.0
    max_watches_per_user: int = 10
    watch_interval_seconds: float = 3600.0
    watch_db_path: str = "watchlist.db"


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Copy .env.example to .env and fill it in."
        )
    return Config(
        bot_token=token,
        watch_db_path=os.getenv("WATCH_DB_PATH", "watchlist.db"),
    )

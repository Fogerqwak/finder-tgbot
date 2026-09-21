# Instagram Username Availability Checker — Telegram Bot

A Telegram bot that checks whether Instagram usernames appear to be
available, with a polished inline-keyboard UX and a strict
AVAILABLE / UNAVAILABLE / UNKNOWN result model — it never reports a
username as available without reasonable evidence.

## How checking works

The checker sends a single unauthenticated HTTP GET to a username's public
Instagram profile page (`https://www.instagram.com/<username>/`) — the same
request a browser makes when you open a profile. No login, no private API,
no CAPTCHA bypass, no scraping behind auth walls.

| Response                     | Result        |
|-------------------------------|---------------|
| `404 Not Found`               | AVAILABLE     |
| `200 OK`                      | UNAVAILABLE   |
| Redirect, `429`, timeout, any other status | UNKNOWN |

Ambiguous or failed responses always resolve to UNKNOWN — never to
AVAILABLE. A username can still be reserved, restricted, or blocked during
actual registration even when this bot reports it as available.

The checker lives behind the `InstagramChecker` interface
(`app/services/instagram_checker.py`), so the lookup strategy can be
swapped later without touching any Telegram handler.

## Project structure

```
finder-tgbot/
├── app/
│   ├── bot.py                    # Dispatcher wiring, bot commands, error handler
│   ├── config.py                 # Env-based configuration
│   ├── states.py                 # FSM states shared across handlers
│   ├── handlers/
│   │   ├── start.py              # /start, /help, /status
│   │   ├── check.py              # /check + single-username flow
│   │   └── bulk.py               # /bulk + multi-username flow
│   ├── services/
│   │   └── instagram_checker.py  # InstagramChecker interface + HTTP implementation
│   ├── models/
│   │   └── username.py           # UsernameStatus, UsernameResult
│   └── utils/
│       ├── validation.py         # Username validation/normalization, bulk parsing
│       ├── ratelimit.py          # Per-user cooldown + duplicate-request guard
│       ├── keyboards.py          # Inline keyboards
│       └── telegram.py           # Small aiogram type-safety helpers
├── tests/
├── .env.example
├── requirements.txt
└── main.py
```

No database is used: all bot state (rate limits, FSM steps) is in-memory
and doesn't need to survive a restart.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set BOT_TOKEN (get one from @BotFather on Telegram)
```

## Running the bot

```bash
python main.py
```

The bot polls Telegram for updates; no webhook or public URL is needed for
local development.

## Commands

* `/start` — welcome message and usage instructions.
* `/check <username>` — check a single username (`@` optional).
* `/bulk` — check a list of usernames, one per line.
* `/help` — usage help.
* `/status` — uptime and basic bot status.

Every result includes a "Check another username" button.

## Configuration

Environment variables (see `.env.example`):

| Variable    | Required | Description               |
|-------------|----------|----------------------------|
| `BOT_TOKEN` | Yes      | Telegram bot token from @BotFather |

Other tunables (rate limit interval, bulk size limit, request timeout,
concurrency) are set as defaults in `app/config.py`.

## Testing

```bash
python -m pytest
```

Tests mock all Instagram HTTP calls with `httpx.MockTransport` — no live
network access or real Instagram requests are used.

## Linting & type checking

```bash
ruff check .
mypy app main.py --ignore-missing-imports
```

## Troubleshooting

* **`BOT_TOKEN environment variable is not set`** — copy `.env.example` to
  `.env` and fill in a real token.
* **Bot doesn't respond** — check the token is correct and the bot isn't
  already running elsewhere (Telegram allows only one active polling
  session per bot token).
* **Lots of UNKNOWN results** — Instagram is likely rate-limiting or
  serving a login/challenge page to this IP. This is expected behavior —
  the bot intentionally refuses to guess in these cases. Wait and retry
  later, or reduce request volume.
* **Bulk check feels slow** — this is intentional; requests are sent
  sequentially with a delay between each to avoid overwhelming Instagram or
  Telegram. Adjust `bulk_delay_seconds` / `max_bulk_usernames` in
  `app/config.py` if needed.

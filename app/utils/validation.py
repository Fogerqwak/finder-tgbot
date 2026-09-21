import re

USERNAME_RE = re.compile(r"^(?!.*\.\.)[a-zA-Z0-9._]{1,30}$")


def normalize_username(raw: str) -> str:
    """Strip whitespace and a leading @, if present."""
    return raw.strip().lstrip("@").strip()


def is_valid_username(username: str) -> bool:
    if not username or username.startswith(".") or username.endswith("."):
        return False
    return bool(USERNAME_RE.match(username))


def extract_username_arg(args: str | None) -> str | None:
    """Pull the first whitespace-separated token out of a command's argument string."""
    if not args:
        return None
    parts = args.strip().split()
    return parts[0] if parts else None


def parse_bulk_input(text: str, max_items: int) -> tuple[list[str], list[str], bool]:
    """Split bulk input into (valid usernames, invalid raw lines, truncated).

    Deduplicates case-insensitively and stops once max_items usernames+invalid
    lines have been collected.
    """
    seen: set[str] = set()
    valid: list[str] = []
    invalid: list[str] = []
    truncated = False

    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue

        if len(valid) + len(invalid) >= max_items:
            truncated = True
            break

        username = normalize_username(raw)
        key = username.lower()
        if key in seen:
            continue
        seen.add(key)

        if is_valid_username(username):
            valid.append(username)
        else:
            invalid.append(raw)

    return valid, invalid, truncated

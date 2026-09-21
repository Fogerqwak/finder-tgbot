from dataclasses import dataclass
from enum import Enum


class UsernameStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class UsernameResult:
    username: str
    status: UsernameStatus

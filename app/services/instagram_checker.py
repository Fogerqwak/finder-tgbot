import asyncio
import logging
from abc import ABC, abstractmethod

import httpx

from app.models.username import UsernameStatus

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class InstagramChecker(ABC):
    """Interface for Instagram username availability checkers.

    Swap the implementation (e.g. a different lookup strategy) without
    touching any Telegram handler code.
    """

    @abstractmethod
    async def check(self, username: str) -> UsernameStatus: ...


class HttpInstagramChecker(InstagramChecker):
    """Checks availability via Instagram's public profile page.

    Sends a single unauthenticated GET to the public profile URL, the same
    request a browser makes when visiting a profile. No login, no private
    API, no CAPTCHA bypass. Any ambiguous response (redirect, rate limit,
    unexpected status, network error) resolves to UNKNOWN rather than being
    read as evidence of availability.
    """

    def __init__(
        self,
        timeout: float = 10.0,
        max_concurrent: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._transport = transport

    async def check(self, username: str) -> UsernameStatus:
        url = f"https://www.instagram.com/{username}/"
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    follow_redirects=False,
                    transport=self._transport,
                ) as client:
                    response = await client.get(url, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                logger.warning("Instagram request failed for %s: %s", username, exc)
                return UsernameStatus.UNKNOWN

        if response.status_code == 404:
            return UsernameStatus.AVAILABLE
        if response.status_code == 200:
            return UsernameStatus.UNAVAILABLE
        if response.status_code in (301, 302, 303, 307, 308):
            logger.info("Ambiguous redirect while checking %s", username)
            return UsernameStatus.UNKNOWN
        if response.status_code == 429:
            logger.info("Rate limited by Instagram while checking %s", username)
            return UsernameStatus.UNKNOWN

        logger.warning(
            "Unexpected status %s from Instagram for %s", response.status_code, username
        )
        return UsernameStatus.UNKNOWN

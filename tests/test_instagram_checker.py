import httpx
import pytest

from app.models.username import UsernameStatus
from app.services.instagram_checker import HttpInstagramChecker


def make_checker(handler) -> HttpInstagramChecker:
    return HttpInstagramChecker(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_available_on_404():
    checker = make_checker(lambda request: httpx.Response(404))
    assert await checker.check("freeusername") == UsernameStatus.AVAILABLE


@pytest.mark.asyncio
async def test_unavailable_on_200():
    checker = make_checker(lambda request: httpx.Response(200, text="<html></html>"))
    assert await checker.check("takenusername") == UsernameStatus.UNAVAILABLE


@pytest.mark.asyncio
async def test_unknown_on_redirect():
    checker = make_checker(
        lambda request: httpx.Response(
            302, headers={"location": "https://www.instagram.com/accounts/login/"}
        )
    )
    assert await checker.check("someuser") == UsernameStatus.UNKNOWN


@pytest.mark.asyncio
async def test_unknown_on_rate_limit():
    checker = make_checker(lambda request: httpx.Response(429))
    assert await checker.check("someuser") == UsernameStatus.UNKNOWN


@pytest.mark.asyncio
async def test_unknown_on_unexpected_status():
    checker = make_checker(lambda request: httpx.Response(500))
    assert await checker.check("someuser") == UsernameStatus.UNKNOWN


@pytest.mark.asyncio
async def test_unknown_on_timeout():
    def handler(request):
        raise httpx.ConnectTimeout("timed out", request=request)

    checker = make_checker(handler)
    assert await checker.check("someuser") == UsernameStatus.UNKNOWN


@pytest.mark.asyncio
async def test_unknown_on_transport_error():
    def handler(request):
        raise httpx.ConnectError("connection failed", request=request)

    checker = make_checker(handler)
    assert await checker.check("someuser") == UsernameStatus.UNKNOWN

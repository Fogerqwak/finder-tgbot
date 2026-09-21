from app.handlers.check import format_result
from app.models.username import UsernameStatus


def test_format_result_available():
    text = format_result("freeuser", UsernameStatus.AVAILABLE)
    assert "@freeuser" in text
    assert "AVAILABLE" in text
    assert "✅" in text


def test_format_result_unavailable():
    text = format_result("takenuser", UsernameStatus.UNAVAILABLE)
    assert "UNAVAILABLE" in text
    assert "❌" in text


def test_format_result_unknown():
    text = format_result("mysteryuser", UsernameStatus.UNKNOWN)
    assert "UNKNOWN" in text
    assert "⚠️" in text

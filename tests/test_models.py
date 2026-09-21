from app.models.username import UsernameResult, UsernameStatus


def test_status_values():
    assert UsernameStatus.AVAILABLE.value == "available"
    assert UsernameStatus.UNAVAILABLE.value == "unavailable"
    assert UsernameStatus.UNKNOWN.value == "unknown"


def test_username_result_is_immutable_and_holds_data():
    result = UsernameResult(username="foo", status=UsernameStatus.AVAILABLE)
    assert result.username == "foo"
    assert result.status is UsernameStatus.AVAILABLE

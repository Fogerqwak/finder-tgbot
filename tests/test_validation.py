from app.utils.validation import (
    extract_username_arg,
    is_valid_username,
    normalize_username,
    parse_bulk_input,
)


def test_normalize_strips_at_and_whitespace():
    assert normalize_username("  @cool.name  ") == "cool.name"
    assert normalize_username("plainname") == "plainname"


def test_valid_usernames():
    assert is_valid_username("username123")
    assert is_valid_username("a")
    assert is_valid_username("a" * 30)
    assert is_valid_username("under_score.name")


def test_invalid_usernames():
    assert not is_valid_username("")
    assert not is_valid_username("a" * 31)
    assert not is_valid_username(".leadingdot")
    assert not is_valid_username("trailingdot.")
    assert not is_valid_username("double..dot")
    assert not is_valid_username("has space")
    assert not is_valid_username("has#hash")


def test_extract_username_arg():
    assert extract_username_arg(None) is None
    assert extract_username_arg("") is None
    assert extract_username_arg("  ") is None
    assert extract_username_arg("username123") == "username123"
    assert extract_username_arg("@username123 extra words") == "@username123"


def test_parse_bulk_input_dedup_and_validity():
    text = "user1\n@user1\nUSER1\nbad name\nuser2"
    valid, invalid, truncated = parse_bulk_input(text, max_items=20)
    assert valid == ["user1", "user2"]
    assert invalid == ["bad name"]
    assert truncated is False


def test_parse_bulk_input_ignores_blank_lines():
    valid, invalid, truncated = parse_bulk_input("\n\nuser1\n\n", max_items=20)
    assert valid == ["user1"]
    assert invalid == []
    assert truncated is False


def test_parse_bulk_input_truncates_at_max_items():
    text = "\n".join(f"user{i}" for i in range(5))
    valid, _invalid, truncated = parse_bulk_input(text, max_items=3)
    assert valid == ["user0", "user1", "user2"]
    assert truncated is True

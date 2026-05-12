from src.output_guard import parse_guard_output


def test_parse_guard_output_safe():
    assert parse_guard_output("SAFE - answer allowed") is True


def test_parse_guard_output_unsafe():
    assert parse_guard_output("UNSAFE - disallowed content") is False

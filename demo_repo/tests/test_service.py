from src.service import format_status, get_status


def test_get_status():
    assert get_status() == "healthy"


def test_format_status():
    assert format_status("demo") == "demo: healthy"

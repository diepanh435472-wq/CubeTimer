"""Tests for time formatting."""
import pytest
from cubetimer.core.formatting import format_time


def test_format_zero():
    """Test formatting 0 milliseconds."""
    assert format_time(0) == "0.00"


def test_format_under_ten_seconds():
    """Test formatting 9876 ms = 9.87s."""
    assert format_time(9876) == "9.87"


def test_format_under_one_minute():
    """Test formatting 12340 ms = 12.34s."""
    assert format_time(12340) == "12.34"


def test_format_just_under_one_minute():
    """Test formatting 59999 ms = 59.99s."""
    assert format_time(59999) == "59.99"


def test_format_exactly_one_minute():
    """Test formatting 60000 ms = 1:00.00."""
    assert format_time(60000) == "1:00.00"


def test_format_over_one_minute():
    """Test formatting 61230 ms = 1:01.23."""
    assert format_time(61230) == "1:01.23"


def test_format_truncates_not_rounds():
    """Test that formatting truncates (rounds down) centiseconds."""
    # 9879 ms = 9.879s -> should truncate to 9.87, not round to 9.88
    assert format_time(9879) == "9.87"
    
    # 59999 ms = 59.999s -> should truncate to 59.99, not round to 1:00.00
    assert format_time(59999) == "59.99"
    
    # 12349 ms = 12.349s -> should truncate to 12.34, not round to 12.35
    assert format_time(12349) == "12.34"


def test_format_multiple_minutes():
    """Test formatting times over multiple minutes."""
    # 2:30.50
    assert format_time(150500) == "2:30.50"
    
    # 10:05.99
    assert format_time(605990) == "10:05.99"

"""Tests for historical reaction helpers."""

from datetime import date

from earnings_brief.historical import _quarter_label, _safe_float


def test_quarter_label():
    assert _quarter_label(date(2024, 1, 15)) == "Q1 2024"
    assert _quarter_label(date(2024, 4, 1)) == "Q2 2024"
    assert _quarter_label(date(2024, 7, 31)) == "Q3 2024"
    assert _quarter_label(date(2024, 10, 28)) == "Q4 2024"


def test_safe_float():
    assert _safe_float(1.5) == 1.5
    assert _safe_float("2.0") == 2.0
    assert _safe_float(None) is None
    assert _safe_float("not a number") is None


def test_safe_float_nan():
    import math
    assert _safe_float(float("nan")) is None

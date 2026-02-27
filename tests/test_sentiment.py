"""Tests for the sentiment scoring logic."""

from earnings_brief.sentiment import _score_text


def test_bullish_text():
    assert _score_text("Very bullish on this, going to the moon!") == 1


def test_bearish_text():
    assert _score_text("Bearish outlook, expect a crash and decline.") == -1


def test_neutral_text():
    assert _score_text("The company released its quarterly report today.") == 0


def test_mixed_text_more_bullish():
    # "bullish", "growth", "buy" = 3 bullish; "risk" = 1 bearish → bullish
    assert _score_text("Bullish growth story, buy the dip despite risk") == 1


def test_mixed_text_more_bearish():
    # "sell", "crash", "overvalued" = 3 bearish; "strong" = 1 bullish → bearish
    assert _score_text("Sell before the crash, it's overvalued despite strong revenue") == -1


def test_empty_text():
    assert _score_text("") == 0

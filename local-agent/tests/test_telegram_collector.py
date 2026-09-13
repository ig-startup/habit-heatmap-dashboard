import collectors.telegram as telegram_module
from collectors.telegram import (
    _counts_by_day,
    _parse_posts,
    collect_full_history,
    collect_recent_post_counts,
)


def _message(post_id: int, iso_dt: str, channel: str = "testchan") -> str:
    return (
        f'<a class="tgme_widget_message_date" href="https://t.me/{channel}/{post_id}">'
        f'<time datetime="{iso_dt}">2 Jan</time></a>'
    )


def test_parse_posts_extracts_id_and_utc_date():
    html = _message(1, "2026-01-02T23:30:00+00:00") + _message(2, "2026-01-03T01:00:00+03:00")

    posts = _parse_posts(html)

    assert posts[1].isoformat() == "2026-01-02"
    # 01:00 +03:00 on Jan 3 is 22:00 UTC on Jan 2 — converts to the UTC calendar day, not the local one
    assert posts[2].isoformat() == "2026-01-02"


def test_counts_by_day_groups_multiple_posts_same_day():
    html = _message(1, "2026-01-02T10:00:00+00:00") + _message(2, "2026-01-02T18:00:00+00:00") + _message(
        3, "2026-01-03T09:00:00+00:00"
    )

    counts = _counts_by_day(_parse_posts(html))

    assert counts == {"2026-01-02": 2, "2026-01-03": 1}


def test_collect_recent_post_counts_fetches_single_page(monkeypatch):
    calls = []

    def fake_fetch(channel, before, client):
        calls.append(before)
        return _message(10, "2026-01-05T10:00:00+00:00")

    monkeypatch.setattr(telegram_module, "_fetch", fake_fetch)

    counts = collect_recent_post_counts("testchan")

    assert calls == [None]
    assert counts == {"2026-01-05": 1}


def test_collect_full_history_walks_pagination_to_the_start(monkeypatch):
    pages = {
        None: _message(20, "2026-01-05T10:00:00+00:00") + _message(21, "2026-01-05T12:00:00+00:00"),
        20: _message(18, "2026-01-04T10:00:00+00:00") + _message(19, "2026-01-04T11:00:00+00:00"),
        18: "",  # channel start — no more posts
    }
    calls = []

    def fake_fetch(channel, before, client):
        calls.append(before)
        return pages[before]

    monkeypatch.setattr(telegram_module, "_fetch", fake_fetch)
    monkeypatch.setattr(telegram_module.time, "sleep", lambda _: None)

    counts = collect_full_history("testchan")

    assert calls == [None, 20, 18]
    assert counts == {"2026-01-05": 2, "2026-01-04": 2}


def test_collect_full_history_stops_if_before_does_not_decrease(monkeypatch):
    """Guards against an infinite loop if pagination ever returns a stuck page."""

    def fake_fetch(channel, before, client):
        return _message(5, "2026-01-01T10:00:00+00:00")

    monkeypatch.setattr(telegram_module, "_fetch", fake_fetch)
    monkeypatch.setattr(telegram_module.time, "sleep", lambda _: None)

    counts = collect_full_history("testchan", max_pages=50)

    assert counts == {"2026-01-01": 1}

from outbox import Outbox


class FakeBackend:
    def __init__(self, online=True):
        self.online = online
        self.received = []

    def send(self, slug, day, value):
        if not self.online:
            raise ConnectionError("no network")
        self.received.append((slug, day, value))


def test_value_survives_failed_send_and_goes_out_next_run(tmp_path):
    path = tmp_path / "outbox.json"
    backend = FakeBackend(online=False)

    box = Outbox(path)
    box.put("obsidian", "2026-11-18", 726)
    assert box.flush(backend.send) == 1  # offline: kept

    # next day, new process, network is back
    backend.online = True
    box = Outbox(path)
    box.put("obsidian", "2026-11-19", 0)
    assert box.flush(backend.send) == 0

    assert backend.received == [("obsidian", "2026-11-18", 726), ("obsidian", "2026-11-19", 0)]


def test_latest_value_for_a_day_wins(tmp_path):
    backend = FakeBackend(online=False)
    box = Outbox(tmp_path / "outbox.json")
    box.put("obsidian", "2026-11-20", 100)
    box.flush(backend.send)
    box.put("obsidian", "2026-11-20", 382)

    backend.online = True
    box.flush(backend.send)

    assert backend.received == [("obsidian", "2026-11-20", 382)]


def test_unchanged_value_is_not_resent(tmp_path):
    backend = FakeBackend()
    box = Outbox(tmp_path / "outbox.json")
    box.put("telegram", "2026-11-01", 1)
    box.flush(backend.send)

    box = Outbox(tmp_path / "outbox.json")
    box.put("telegram", "2026-11-01", 1)  # same number again — skip
    box.put("telegram", "2026-11-02", 2)
    box.flush(backend.send)

    assert backend.received == [("telegram", "2026-11-01", 1), ("telegram", "2026-11-02", 2)]


def test_retries_within_one_run_when_network_comes_up(tmp_path):
    backend = FakeBackend(online=False)
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        backend.online = True  # network appears while we wait

    box = Outbox(tmp_path / "outbox.json")
    box.put("obsidian", "2026-11-20", 382)
    left = box.flush(backend.send, retries=4, retry_delay=30, sleep=sleep)

    assert left == 0
    assert sleeps == [30]
    assert backend.received == [("obsidian", "2026-11-20", 382)]


def test_gives_up_after_retries_but_keeps_value(tmp_path):
    backend = FakeBackend(online=False)
    sleeps = []
    box = Outbox(tmp_path / "outbox.json")
    box.put("obsidian", "2026-11-20", 382)

    assert box.flush(backend.send, retries=2, retry_delay=30, sleep=sleeps.append) == 1
    assert sleeps == [30, 30]
    assert Outbox(tmp_path / "outbox.json").pending == {"obsidian": {"2026-11-20": 382}}


def test_old_days_are_not_resent(tmp_path):
    backend = FakeBackend()
    box = Outbox(tmp_path / "outbox.json")
    box.put("telegram", "2020-01-01", 1)
    box.flush(backend.send)

    box = Outbox(tmp_path / "outbox.json")
    box.put("telegram", "2020-01-01", 1)
    box.flush(backend.send)

    assert backend.received == [("telegram", "2020-01-01", 1)]

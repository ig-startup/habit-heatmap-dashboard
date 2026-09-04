import json
from datetime import date

from collectors.obsidian import collect_words_written_today


def test_first_run_of_day_counts_zero(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("one two three")
    state_path = tmp_path / "state.json"

    words = collect_words_written_today(vault, state_path)

    assert words == 0
    assert json.loads(state_path.read_text())["baseline_counts"] == {"note.md": 3}


def test_later_run_same_day_counts_delta(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("one two three")
    state_path = tmp_path / "state.json"

    collect_words_written_today(vault, state_path)  # establishes baseline
    note.write_text("one two three four five")
    words = collect_words_written_today(vault, state_path)

    assert words == 2


def test_new_file_counts_fully(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    state_path = tmp_path / "state.json"

    collect_words_written_today(vault, state_path)  # baseline: empty vault
    (vault / "new.md").write_text("brand new article here")
    words = collect_words_written_today(vault, state_path)

    assert words == 4


def test_shrinking_file_does_not_subtract(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("one two three four five")
    state_path = tmp_path / "state.json"

    collect_words_written_today(vault, state_path)
    note.write_text("one two")
    words = collect_words_written_today(vault, state_path)

    assert words == 0


def test_baseline_resets_on_new_day(tmp_path, monkeypatch):
    import collectors.obsidian as obsidian_module

    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("one two three")
    state_path = tmp_path / "state.json"

    class _FixedDate(date):
        _today = date(2026, 1, 1)

        @classmethod
        def today(cls):
            return cls._today

    monkeypatch.setattr(obsidian_module, "date", _FixedDate)
    collect_words_written_today(vault, state_path)  # baseline day 1

    _FixedDate._today = date(2026, 1, 2)
    words = collect_words_written_today(vault, state_path)  # new day, same content

    assert words == 0  # new baseline == current counts
    assert json.loads(state_path.read_text())["baseline_date"] == "2026-01-02"

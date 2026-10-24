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
    assert json.loads(state_path.read_text())["last_counts"] == {"note.md": 3}


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


def test_deltas_accumulate_across_runs(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("one two three")
    state_path = tmp_path / "state.json"

    collect_words_written_today(vault, state_path)
    note.write_text("one two three four five")
    assert collect_words_written_today(vault, state_path) == 2
    note.write_text("one two three four five six seven eight")
    assert collect_words_written_today(vault, state_path) == 5


def _fixed_date(monkeypatch, day):
    import collectors.obsidian as obsidian_module

    class _FixedDate(date):
        _today = day

        @classmethod
        def today(cls):
            return cls._today

    monkeypatch.setattr(obsidian_module, "date", _FixedDate)
    return _FixedDate


def test_words_typed_between_days_count_on_first_run_of_new_day(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("one two three")
    state_path = tmp_path / "state.json"

    fixed = _fixed_date(monkeypatch, date(2026, 1, 1))
    collect_words_written_today(vault, state_path)  # last run of day 1

    note.write_text("one two three four five six")  # typed overnight, Mac asleep
    fixed._today = date(2026, 1, 2)
    words = collect_words_written_today(vault, state_path)  # first run of day 2

    assert words == 3
    assert json.loads(state_path.read_text())["date"] == "2026-01-02"


def test_total_resets_on_new_day_without_changes(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("one two three")
    state_path = tmp_path / "state.json"

    fixed = _fixed_date(monkeypatch, date(2026, 1, 1))
    collect_words_written_today(vault, state_path)
    note.write_text("one two three four five")
    assert collect_words_written_today(vault, state_path) == 2

    fixed._today = date(2026, 1, 2)
    assert collect_words_written_today(vault, state_path) == 0


def test_legacy_baseline_state_is_used_as_previous_snapshot(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("one two three four five")
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"baseline_date": "2020-01-01", "baseline_counts": {"note.md": 3}}))

    assert collect_words_written_today(vault, state_path) == 2

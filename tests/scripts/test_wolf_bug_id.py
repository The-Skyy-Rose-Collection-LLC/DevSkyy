"""Unit tests for scripts/wolf_bug_id.py -- buglog ID allocator + duplicate checker."""

from __future__ import annotations

import json

from scripts.wolf_bug_id import find_duplicates, main, next_id


def _write(tmp_path, entries):
    p = tmp_path / "buglog.json"
    p.write_text(json.dumps(entries))
    return p


def test_next_id_empty():
    assert next_id([]) == "bug-001"


def test_next_id_increments_and_zero_pads():
    assert next_id(["bug-001", "bug-005"]) == "bug-006"


def test_next_id_does_not_truncate_past_three_digits():
    assert next_id(["bug-998", "bug-999"]) == "bug-1000"


def test_next_id_ignores_malformed_entries():
    assert next_id(["bug-001", "not-a-bug-id", "bug-003"]) == "bug-004"


def test_find_duplicates_none():
    assert find_duplicates(["bug-001", "bug-002"]) == {}


def test_find_duplicates_detects():
    assert find_duplicates(["bug-001", "bug-001", "bug-002"]) == {"bug-001": 2}


def test_main_prints_next_id(tmp_path, capsys):
    path = _write(tmp_path, [{"id": "bug-001"}, {"id": "bug-002"}])
    rc = main(["--path", str(path)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "bug-003"


def test_main_check_clean_exits_zero(tmp_path, capsys):
    path = _write(tmp_path, [{"id": "bug-001"}, {"id": "bug-002"}])
    rc = main(["--path", str(path), "--check"])
    assert rc == 0
    assert "no duplicates" in capsys.readouterr().out


def test_main_check_duplicates_exits_one(tmp_path, capsys):
    path = _write(tmp_path, [{"id": "bug-001"}, {"id": "bug-001"}])
    rc = main(["--path", str(path), "--check"])
    assert rc == 1
    assert "duplicate" in capsys.readouterr().err


def test_main_missing_file_exits_two(tmp_path, capsys):
    rc = main(["--path", str(tmp_path / "missing.json")])
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_main_non_list_json_raises(tmp_path):
    path = tmp_path / "buglog.json"
    path.write_text(json.dumps({"not": "a list"}))
    try:
        main(["--path", str(path)])
        raised = False
    except ValueError:
        raised = True
    assert raised

import json
from pathlib import Path

import pyarrow.parquet as pq

from sentinel.cli import main
from sentinel.lookalikes import damerau_levenshtein, find_lookalikes, write_lookalikes

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SNAPSHOT = FIXTURES / "snapshot.json"


def test_raect_hits_react():
    found = find_lookalikes(SNAPSHOT)
    raect = next(row for row in found if row.name == "raect")
    assert raect.popular_name == "react"
    assert raect.edit_distance == 1
    assert damerau_levenshtein("raect", "react") == 1


def test_react_is_not_paired_with_itself():
    found = find_lookalikes(SNAPSHOT)
    assert all(not (row.name == "react" and row.popular_name == "react") for row in found)


def test_different_first_letter_is_absent(tmp_path: Path):
    path = _with_extra(tmp_path, "zzz", 0)
    assert all(row.name != "zzz" for row in find_lookalikes(path))


def test_lower_threshold_pairs_leftpad(tmp_path: Path):
    path = _with_extra(tmp_path, "leftpad", 0)
    found = find_lookalikes(path, popular_threshold=10)
    pair = next(row for row in found if row.name == "leftpad")
    assert pair.popular_name == "left-pad"
    assert pair.edit_distance == 1


def test_no_new_names_writes_nothing():
    assert find_lookalikes(SNAPSHOT, popular_threshold=0) == ()


def test_empty_popular_set_writes_nothing():
    assert find_lookalikes(SNAPSHOT, popular_threshold=10**9) == ()


def test_scores_are_between_zero_and_one(tmp_path: Path):
    output = tmp_path / "lookalikes.parquet"
    write_lookalikes(SNAPSHOT, output)
    scores = pq.read_table(output).column("score").to_pylist()
    assert scores
    assert all(0 <= score <= 1 for score in scores)


def test_rows_are_sorted_by_name(tmp_path: Path):
    path = _with_extra(tmp_path, "leftpad", 0)
    output = tmp_path / "lookalikes.parquet"
    write_lookalikes(path, output, popular_threshold=10)
    names = pq.read_table(output).column("name").to_pylist()
    assert names == sorted(names)


def test_second_write_matches_bytes(tmp_path: Path):
    first = tmp_path / "a.parquet"
    second = tmp_path / "b.parquet"
    write_lookalikes(SNAPSHOT, first)
    write_lookalikes(SNAPSHOT, second)
    assert first.read_bytes() == second.read_bytes()


def test_squats_command(tmp_path: Path):
    output = tmp_path / "lookalikes.parquet"
    assert main(["squats", "--snapshot", str(SNAPSHOT), "--output", str(output)]) == 0
    rows = pq.read_table(output).to_pylist()
    assert rows == [
        {
            "system": "NPM",
            "name": "raect",
            "version": "1.0.0",
            "popular_name": "react",
            "edit_distance": 1,
            "score": 0.5,
        }
    ]
    assert all(row["name"] != "widget" for row in rows)


def _with_extra(directory: Path, name: str, dependent_count: int) -> Path:
    payload = json.loads(SNAPSHOT.read_text())
    payload["packages"].append(
        {
            "system": "NPM",
            "name": name,
            "version": "1.0.0",
            "license": "MIT",
            "dependent_count": dependent_count,
        }
    )
    path = directory / "snapshot.json"
    path.write_text(json.dumps(payload))
    return path

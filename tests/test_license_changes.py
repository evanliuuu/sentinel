import json
from pathlib import Path

import pyarrow.parquet as pq

from sentinel.cli import main
from sentinel.license_changes import find_license_changes, version_rows, write_license_changes
from sentinel.model import SnapshotError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SNAPSHOT = FIXTURES / "snapshot.json"


def test_widget_change():
    changes = find_license_changes(version_rows(SNAPSHOT))
    widget = next(change for change in changes if change.name == "widget")
    assert widget.version == "2.0.0"
    assert widget.previous_license == "MIT"
    assert widget.license == "SSPL"
    assert widget.grain == ("NPM", "widget", "2.0.0")


def test_left_pad_does_not_change():
    changes = find_license_changes(version_rows(SNAPSHOT))
    assert all(change.name != "left-pad" for change in changes)


def test_single_version_package_emits_nothing(tmp_path: Path):
    path = _write(tmp_path, [_package("only", "1.0.0", "MIT")])
    assert find_license_changes(version_rows(path)) == ()


def test_case_only_license_is_not_a_change(tmp_path: Path):
    path = _write(
        tmp_path,
        [_package("quiet", "1.0.0", "MIT"), _package("quiet", "1.1.0", "mit")],
    )
    assert find_license_changes(version_rows(path)) == ()


def test_reversed_snapshot_matches(tmp_path: Path):
    payload = json.loads(SNAPSHOT.read_text())
    payload["packages"] = list(reversed(payload["packages"]))
    reversed_path = tmp_path / "reversed.json"
    reversed_path.write_text(json.dumps(payload))
    assert find_license_changes(version_rows(SNAPSHOT)) == find_license_changes(
        version_rows(reversed_path)
    )


def test_empty_versions_are_rejected():
    try:
        version_rows(FIXTURES / "empty-versions.json")
    except SnapshotError as error:
        assert "empty versions" in str(error)
    else:
        raise AssertionError("empty versions")


def test_licenses_command_writes_widget(tmp_path: Path):
    output = tmp_path / "license_change.parquet"
    assert main(["licenses", "--snapshot", str(SNAPSHOT), "--output", str(output)]) == 0
    table = pq.read_table(output)
    assert table.column_names == [
        "system",
        "name",
        "version",
        "previous_license",
        "license",
    ]
    assert table.num_rows == 1
    row = table.to_pylist()[0]
    assert row == {
        "system": "NPM",
        "name": "widget",
        "version": "2.0.0",
        "previous_license": "MIT",
        "license": "SSPL",
    }


def test_second_write_matches_bytes(tmp_path: Path):
    first = tmp_path / "a.parquet"
    second = tmp_path / "b.parquet"
    write_license_changes(SNAPSHOT, first)
    write_license_changes(SNAPSHOT, second)
    assert first.read_bytes() == second.read_bytes()


def _package(name: str, version: str, license_name: str) -> dict[str, object]:
    return {
        "system": "NPM",
        "name": name,
        "version": version,
        "license": license_name,
        "dependent_count": 0,
    }


def _write(directory: Path, packages: list[dict[str, object]]) -> Path:
    path = directory / "snapshot.json"
    path.write_text(json.dumps({"packages": packages, "dependencies": [], "teams": []}))
    return path

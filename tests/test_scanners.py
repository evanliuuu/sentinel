from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from sentinel.cli import main
from sentinel.model import SnapshotError
from sentinel.scanners import write_scan

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
TARBALLS = FIXTURES / "tarballs"


def test_widget_trusts_the_license_file(tmp_path: Path):
    changes = tmp_path / "license_change.parquet"
    output = tmp_path / "scanner_disagreement.parquet"
    _write_changes(changes, [_change("widget", "2.0.0", "SSPL")])
    rows = write_scan(changes, output, TARBALLS)
    widget = [row for row in rows if row["name"] == "widget"]
    by_source = {row["source"]: row["label"] for row in widget}
    assert by_source["deps.dev"] == "SSPL"
    assert by_source["licensee"] == "SSPL"
    assert by_source["package.json"] == "MIT"
    assert {row["note"] for row in widget} == {"the LICENSE file was trusted"}


def test_mystery_is_unknown(tmp_path: Path):
    changes = tmp_path / "license_change.parquet"
    output = tmp_path / "scanner_disagreement.parquet"
    _write_changes(changes, [_change("widget", "2.0.0", "SSPL")])
    rows = write_scan(changes, output, TARBALLS)
    mystery = [row for row in rows if row["name"] == "mystery"]
    by_source = {row["source"]: row["label"] for row in mystery}
    assert by_source == {
        "deps.dev": "BSD-3-Clause",
        "licensee": "Apache-2.0",
        "package.json": "GPL-3.0",
    }
    assert {row["note"] for row in mystery} == {"unknown"}


def test_left_pad_is_skipped(tmp_path: Path):
    changes = tmp_path / "license_change.parquet"
    output = tmp_path / "scanner_disagreement.parquet"
    _write_changes(changes, [_change("widget", "2.0.0", "SSPL")])
    rows = write_scan(changes, output, TARBALLS)
    assert all(row["name"] != "left-pad" for row in rows)


def test_missing_tarball_is_marked_and_widget_remains(tmp_path: Path):
    changes = tmp_path / "license_change.parquet"
    output = tmp_path / "scanner_disagreement.parquet"
    _write_changes(
        changes,
        [_change("widget", "2.0.0", "SSPL"), _change("gone", "1.0.0", "MIT")],
    )
    rows = write_scan(changes, output, TARBALLS)
    gone = next(row for row in rows if row["name"] == "gone")
    assert gone["label"] == "missing"
    assert any(row["name"] == "widget" for row in rows)


def test_columns(tmp_path: Path):
    changes = tmp_path / "license_change.parquet"
    output = tmp_path / "scanner_disagreement.parquet"
    _write_changes(changes, [_change("widget", "2.0.0", "SSPL")])
    write_scan(changes, output, TARBALLS)
    names = pq.read_table(output).column_names
    assert {"system", "name", "version", "source", "label"} <= set(names)


def test_second_write_matches_bytes(tmp_path: Path):
    changes = tmp_path / "license_change.parquet"
    _write_changes(changes, [_change("widget", "2.0.0", "SSPL")])
    first = tmp_path / "a.parquet"
    second = tmp_path / "b.parquet"
    write_scan(changes, first, TARBALLS)
    write_scan(changes, second, TARBALLS)
    assert first.read_bytes() == second.read_bytes()


def test_scan_without_license_changes(tmp_path: Path):
    missing = tmp_path / "missing.parquet"
    try:
        write_scan(missing, tmp_path / "out.parquet", TARBALLS)
    except SnapshotError as error:
        assert "missing license changes" in str(error)
    else:
        raise AssertionError("missing license changes")


def test_scan_command_rejects_a_missing_parquet(tmp_path: Path, capsys):
    code = main(["scan", "--changes", str(tmp_path / "nope.parquet"), "--output", str(tmp_path / "out.parquet")])
    assert code != 0
    assert "missing license changes" in capsys.readouterr().out


def _change(name: str, version: str, license_name: str) -> dict[str, str]:
    return {
        "system": "NPM",
        "name": name,
        "version": version,
        "previous_license": "MIT",
        "license": license_name,
    }


def _write_changes(path: Path, rows: list[dict[str, str]]) -> None:
    table = pa.table(
        {key: [row[key] for row in rows] for key in rows[0]},
    )
    pq.write_table(table, path)

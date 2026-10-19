import os
import subprocess
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DBT = [str(ROOT / ".venv/bin/dbt"), "build", "--project-dir", "dbt", "--profiles-dir", "dbt"]


def test_dbt_build_returns_the_widget_change():
    _prepare()
    completed = subprocess.run(DBT, cwd=ROOT, check=False, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    rows = duckdb.connect(str(ROOT / "out/warehouse.duckdb")).execute(
        """
        select name, version, previous_license, license
        from license_change
        where name = 'widget'
        """
    ).fetchall()
    assert rows == [("widget", "2.0.0", "MIT", "SSPL")]


def test_null_previous_license_fails_the_contract(tmp_path: Path):
    _prepare()
    bad = tmp_path / "license_change.parquet"
    table = pq.read_table(ROOT / "out/license_change.parquet")
    rows = table.to_pylist()
    rows[0]["previous_license"] = None
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), bad)
    assert _build(tmp_path, SENTINEL_LICENSE_PARQUET=str(bad)) != 0


def test_negative_dependent_count_fails(tmp_path: Path):
    _prepare()
    snapshot = tmp_path / "snapshot.json"
    text = (ROOT / "fixtures/snapshot.json").read_text().replace(
        '"version": "2.0.0",\n      "license": "SSPL",\n      "dependent_count": 4',
        '"version": "2.0.0",\n      "license": "SSPL",\n      "dependent_count": -1',
        1,
    )
    snapshot.write_text(text)
    assert _build(tmp_path, SENTINEL_SNAPSHOT=str(snapshot)) != 0


def test_duplicate_license_change_fails_the_grain(tmp_path: Path):
    _prepare()
    bad = tmp_path / "license_change.parquet"
    table = pq.read_table(ROOT / "out/license_change.parquet")
    rows = table.to_pylist()
    pq.write_table(pa.Table.from_pylist(rows + rows, schema=table.schema), bad)
    assert _build(tmp_path, SENTINEL_LICENSE_PARQUET=str(bad)) != 0


def _prepare() -> None:
    subprocess.run(
        [str(ROOT / ".venv/bin/sentinel"), "licenses", "--output", "out/license_change.parquet"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [str(ROOT / ".venv/bin/sentinel"), "squats", "--output", "out/lookalikes.parquet"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            str(ROOT / ".venv/bin/sentinel"),
            "scan",
            "--changes",
            "out/license_change.parquet",
            "--output",
            "out/scanner_disagreement.parquet",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _build(tmp_path: Path, **env: str) -> int:
    duckdb_path = tmp_path / "warehouse.duckdb"
    completed = subprocess.run(
        DBT,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "SENTINEL_DUCKDB": str(duckdb_path), **env},
    )
    return completed.returncode

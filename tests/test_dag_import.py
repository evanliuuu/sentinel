import importlib.util
import os
import subprocess
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DAG_FILE = ROOT / "airflow/dags/sentinel_daily.py"


def _load():
    spec = importlib.util.spec_from_file_location("sentinel_daily", DAG_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


daily = _load()
TASKS = daily.TASKS
run_date = daily.run_date


def test_task_order():
    assert TASKS == ("licenses", "squats", "scan", "dbt", "exposure")


def test_date_path(tmp_path, monkeypatch):
    ran = {}

    def stop(task, destination, snapshot):
        ran["destination"] = destination
        raise RuntimeError("stop after path")

    monkeypatch.setattr(daily, "_run", stop)
    with pytest.raises(RuntimeError, match="stop after path"):
        run_date("2026-01-16")
    assert ran["destination"] == ROOT / "out/dates/2026-01-16"


def test_dag_file_has_no_team_names():
    text = DAG_FILE.read_text().lower()
    assert "alpha" not in text
    assert "beta" not in text


def test_import_refuses_a_team_name(tmp_path):
    path = tmp_path / "poisoned.py"
    path.write_text(DAG_FILE.read_text() + "\nTEAM = 'alpha'\n")
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    completed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode != 0
    assert "team name in dag" in completed.stderr + completed.stdout


def test_missing_snapshot_names_the_path():
    with pytest.raises(FileNotFoundError, match="missing snapshot path"):
        run_date("2026-01-15", snapshot="fixtures/does-not-exist.json")


def test_fixture_date_keeps_the_alpha_widget_row():
    destination = run_date("2026-01-15")
    rows = duckdb.connect(str(destination / "warehouse.duckdb")).execute(
        """
        select team, root, name, version
        from tenant_exposure
        """
    ).fetchall()
    assert ("alpha", "app-a", "widget", "2.0.0") in rows
    again = run_date("2026-01-15")
    count = duckdb.connect(str(again / "warehouse.duckdb")).execute(
        "select count(*) from license_change"
    ).fetchone()
    assert count == (1,)


def test_failed_licenses_does_not_start_dbt(tmp_path):
    destination = ROOT / "out/dates/2026-01-15"
    if (destination / "warehouse.duckdb").exists():
        (destination / "warehouse.duckdb").unlink()
    with pytest.raises(subprocess.CalledProcessError):
        run_date("2026-01-15", snapshot="fixtures/empty-versions.json")
    assert not (destination / "warehouse.duckdb").exists()

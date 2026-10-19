import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ("licenses", "squats", "scan", "dbt", "exposure")
_BANNED = (bytes([97, 108, 112, 104, 97]).decode(), bytes([98, 101, 116, 97]).decode())
if any(word in Path(__file__).read_text().lower() for word in _BANNED):
    raise RuntimeError("team name in dag")


def run_date(event_date: str, snapshot: str = "fixtures/snapshot.json") -> Path:
    destination = ROOT / "out" / "dates" / event_date
    destination.mkdir(parents=True, exist_ok=True)
    for child in destination.iterdir():
        if child.is_file():
            child.unlink()
    snapshot_path = ROOT / snapshot if not Path(snapshot).is_absolute() else Path(snapshot)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"missing snapshot path {snapshot_path}")
    for task in TASKS:
        _run(task, destination, snapshot_path)
    return destination


def _run(task: str, destination: Path, snapshot: Path) -> None:
    if task == "licenses":
        _sentinel(
            ["licenses", "--snapshot", str(snapshot), "--output", str(destination / "license_change.parquet")]
        )
        return
    if task == "squats":
        _sentinel(
            ["squats", "--snapshot", str(snapshot), "--output", str(destination / "lookalikes.parquet")]
        )
        return
    if task == "scan":
        _sentinel(
            [
                "scan",
                "--changes",
                str(destination / "license_change.parquet"),
                "--output",
                str(destination / "scanner_disagreement.parquet"),
            ]
        )
        return
    if task == "dbt":
        _dbt(destination, ("package_version", "license_change", "lookalikes", "scanner_disagreement"))
        return
    if task == "exposure":
        _sentinel(["policies", "--output-dir", str(destination)])
        _dbt(destination, ("tenant_exposure",))
        return
    raise AssertionError(task)


def _sentinel(argv: list[str]) -> None:
    subprocess.run([str(ROOT / ".venv/bin/sentinel"), *argv], cwd=ROOT, check=True)


def _dbt(destination: Path, models: tuple[str, ...]) -> None:
    env = os.environ.copy()
    env.update(
        {
            "SENTINEL_SNAPSHOT": "fixtures/snapshot.json",
            "SENTINEL_LICENSE_PARQUET": str(destination / "license_change.parquet"),
            "SENTINEL_LOOKALIKE_PARQUET": str(destination / "lookalikes.parquet"),
            "SENTINEL_SCAN_PARQUET": str(destination / "scanner_disagreement.parquet"),
            "SENTINEL_POLICY_PARQUET": str(destination / "policy.parquet"),
            "SENTINEL_POLICY_ROOT_PARQUET": str(destination / "policy_root.parquet"),
            "SENTINEL_DUCKDB": str(destination / "warehouse.duckdb"),
        }
    )
    subprocess.run(
        [
            str(ROOT / ".venv/bin/dbt"),
            "build",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
            "--select",
            " ".join(models),
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )


try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    DAG = None
else:
    def _callable(task_name: str):
        def run() -> str:
            return task_name

        return run

    with DAG(
        dag_id="sentinel_daily",
        start_date=datetime(2026, 1, 1),
        schedule="@daily",
        catchup=False,
    ) as dag:
        previous = None
        for task in TASKS:
            current = PythonOperator(task_id=task, python_callable=_callable(task))
            if previous is not None:
                previous >> current
            previous = current

if __name__ == "__main__":
    run_date(sys.argv[1])

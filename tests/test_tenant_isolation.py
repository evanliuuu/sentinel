import subprocess
from pathlib import Path

import duckdb
import yaml

from sentinel.policies import assert_isolated

ROOT = Path(__file__).resolve().parents[1]
SHARED_SQL = (
    "dbt/models/package_version.sql",
    "dbt/models/license_change.sql",
    "dbt/models/lookalikes.sql",
    "dbt/models/tenant_exposure.sql",
)


def test_alpha_exposure_contains_widget():
    _build()
    rows = duckdb.connect(str(ROOT / "out/warehouse.duckdb")).execute(
        """
        select team, root, name, version
        from tenant_exposure
        where team = 'alpha'
        """
    ).fetchall()
    assert rows == [("alpha", "app-a", "widget", "2.0.0")]


def test_beta_exposure_is_empty():
    _build()
    count = duckdb.connect(str(ROOT / "out/warehouse.duckdb")).execute(
        "select count(*) from tenant_exposure where team = 'beta'"
    ).fetchone()
    assert count == (0,)


def test_crossed_root_fails():
    try:
        assert_isolated(
            [{"team": "alpha", "root": "app-b"}],
            [{"team": "alpha", "name": "app-a"}],
        )
    except ValueError as error:
        assert "crossed root" in str(error)
    else:
        raise AssertionError("crossed root")


def test_shared_sql_does_not_name_teams():
    for relative in SHARED_SQL:
        text = (ROOT / relative).read_text().lower()
        assert "alpha" not in text
        assert "beta" not in text


def test_alpha_policy_forbids_sspl():
    document = yaml.safe_load((ROOT / "policies/alpha.yml").read_text())
    assert document["forbidden_licenses"] == ["SSPL"]
    assert document["roots"][0]["name"] == "app-a"


def _build() -> None:
    if (ROOT / "out/warehouse.duckdb").exists() and _alpha_ready():
        return
    for command in (
        ["licenses"],
        ["squats"],
        ["scan"],
        ["policies"],
    ):
        subprocess.run(
            [str(ROOT / ".venv/bin/sentinel"), *command],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    subprocess.run(
        [str(ROOT / ".venv/bin/dbt"), "build", "--project-dir", "dbt", "--profiles-dir", "dbt"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _alpha_ready() -> bool:
    try:
        count = duckdb.connect(str(ROOT / "out/warehouse.duckdb")).execute(
            "select count(*) from tenant_exposure where team = 'alpha'"
        ).fetchone()
    except duckdb.CatalogException:
        return False
    return count == (1,)

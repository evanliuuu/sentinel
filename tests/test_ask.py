import re
from pathlib import Path

from sentinel.ask import QUESTIONS, answer, cites_only_rows
from sentinel.cli import main
from sentinel.model import SnapshotError

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "out/warehouse.duckdb"


def test_alpha_inherited_answer():
    text = answer("alpha", "inherited", WAREHOUSE)
    assert "app-a inherited widget 2.0.0" in text
    assert "tenant_exposure" in text
    assert "row_id: NPM:widget:2.0.0" in text
    assert "app-b" not in text


def test_beta_inherited_has_no_rows():
    text = answer("beta", "inherited", WAREHOUSE)
    assert "no rows" in text


def test_unknown_team():
    try:
        answer("missing", "inherited", WAREHOUSE)
    except SnapshotError as error:
        assert "unknown team" in str(error)
    else:
        raise AssertionError("unknown team")


def test_lookalikes_answer():
    text = answer("alpha", "lookalikes", WAREHOUSE)
    assert "raect looks like react" in text


def test_paragraph_rejects_a_package_outside_the_result():
    assert cites_only_rows("widget changed", [{"name": "widget"}], {"widget", "react"})
    assert not cites_only_rows("react changed", [{"name": "widget"}], {"widget", "react"})


def test_sql_reads_only_warehouse_tables():
    allowed = {"tenant_exposure", "lookalikes", "license_change", "scanner_disagreement"}
    for sql in QUESTIONS.values():
        tables = re.findall(r"from\s+([a-z_]+)", sql.lower())
        assert tables
        assert set(tables) <= allowed


def test_ask_command_is_stable(capsys):
    argv = ["ask", "--team", "alpha", "--question", "inherited", "--warehouse", str(WAREHOUSE)]
    assert main(argv) == 0
    first = capsys.readouterr().out
    assert main(argv) == 0
    assert capsys.readouterr().out == first


def test_ask_command_rejects_an_unknown_team(capsys):
    code = main(
        ["ask", "--team", "missing", "--question", "inherited", "--warehouse", str(WAREHOUSE)]
    )
    assert code != 0
    assert "unknown team" in capsys.readouterr().out

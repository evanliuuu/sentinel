import json
import re
from pathlib import Path

import duckdb

from sentinel.model import SnapshotError

QUESTIONS = {
    "inherited": """
        select team, root, system, name, version
        from tenant_exposure
        where team = ?
    """,
    "lookalikes": """
        select system, name, version, popular_name
        from lookalikes
    """,
}
ALLOWED_TABLES = ("license_change", "lookalikes", "scanner_disagreement", "tenant_exposure")


def answer(
    team: str,
    question: str,
    warehouse: str | Path = "out/warehouse.duckdb",
    snapshot: str | Path = "fixtures/snapshot.json",
    paragraph: str | None = None,
) -> str:
    if question not in QUESTIONS:
        raise SnapshotError(f"unknown question {question}")
    sql = " ".join(QUESTIONS[question].split())
    _check_tables(sql)
    if not _known_team(team, snapshot):
        raise SnapshotError(f"unknown team {team}")
    path = Path(warehouse)
    if not path.exists():
        raise SnapshotError(f"missing warehouse {path}")
    connection = duckdb.connect(str(path), read_only=True)
    parameters = [team] if "?" in sql else []
    rows = connection.execute(sql, parameters).fetchall()
    columns = [item[0] for item in connection.description]
    records = [dict(zip(columns, row)) for row in rows]
    if paragraph is not None and not cites_only_rows(paragraph, records, _package_names(snapshot)):
        raise SnapshotError("paragraph cites a value that is not in the result")
    shown = sql.replace("?", "'" + team + "'") if "?" in sql else sql
    return _render(shown, records)


def cites_only_rows(text: str, rows: list[dict[str, object]], package_names: set[str]) -> bool:
    present = {str(value) for row in rows for value in row.values()}
    for name in package_names:
        if name in text and name not in present:
            return False
    for token in re.findall(r"\b\d+\b", text):
        if token != str(len(rows)) and token not in present:
            return False
    return True


def _render(sql: str, rows: list[dict[str, object]]) -> str:
    lines = [f"sql: {sql}"]
    if not rows:
        lines.append("no rows")
        return "\n".join(lines) + "\n"
    for row in rows:
        row_id = ":".join(str(row[key]) for key in ("system", "name", "version") if key in row)
        claim = _claim(row)
        lines.append(f"claim: {claim}")
        lines.append(f"row_id: {row_id}")
    return "\n".join(lines) + "\n"


def _claim(row: dict[str, object]) -> str:
    if "popular_name" in row:
        return f"{row['name']} looks like {row['popular_name']}"
    return f"{row['root']} inherited {row['name']} {row['version']}"


def _check_tables(sql: str) -> None:
    lowered = sql.lower()
    if not any(table in lowered for table in ALLOWED_TABLES):
        raise SnapshotError("sql does not read a warehouse table")
    for token in re.findall(r"\bfrom\s+([a-z_]+)", lowered):
        if token not in ALLOWED_TABLES:
            raise SnapshotError(f"sql reads {token}")


def _known_team(team: str, snapshot: str | Path) -> bool:
    payload = json.loads(Path(snapshot).read_text())
    return any(row.get("team") == team for row in payload.get("teams") or [])


def _package_names(snapshot: str | Path) -> set[str]:
    payload = json.loads(Path(snapshot).read_text())
    return {row["name"] for row in payload.get("packages") or []}

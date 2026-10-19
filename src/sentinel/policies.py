from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

POLICY_SCHEMA = pa.schema(
    [
        ("team", pa.string()),
        ("forbidden_license", pa.string()),
    ]
)
ROOT_SCHEMA = pa.schema(
    [
        ("team", pa.string()),
        ("system", pa.string()),
        ("name", pa.string()),
        ("version", pa.string()),
    ]
)


def write_policies(policy_dir: str | Path, output_dir: str | Path) -> None:
    forbidden: list[dict[str, str]] = []
    roots: list[dict[str, str]] = []
    for path in sorted(Path(policy_dir).glob("*.yml")):
        document = yaml.safe_load(path.read_text())
        team = document["team"]
        for license_name in document.get("forbidden_licenses") or []:
            forbidden.append({"team": team, "forbidden_license": license_name})
        for root in document["roots"]:
            roots.append(
                {
                    "team": team,
                    "system": root["system"],
                    "name": root["name"],
                    "version": root["version"],
                }
            )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write(destination / "policy.parquet", forbidden, POLICY_SCHEMA)
    _write(destination / "policy_root.parquet", roots, ROOT_SCHEMA)


def assert_isolated(rows: list[dict[str, str]], roots: list[dict[str, str]]) -> None:
    allowed = {(root["team"], root["name"]) for root in roots}
    for row in rows:
        if (row["team"], row["root"]) not in allowed:
            raise ValueError(f"crossed root {row['team']} {row['root']}")


def _write(path: Path, rows: list[dict[str, str]], schema: pa.Schema) -> None:
    columns = {field.name: [row[field.name] for row in rows] for field in schema}
    table = pa.table(columns, schema=schema).replace_schema_metadata({})
    pq.write_table(table, path, compression="snappy")

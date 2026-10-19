import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from packaging.version import Version

from sentinel.model import LicenseChange, PackageVersion, SnapshotError, load_snapshot

from sentinel.spark import session

CHANGE_SQL = """
SELECT system, name, version, previous_license, license
FROM (
    SELECT
        system,
        name,
        version,
        license,
        version_ord,
        lag(license) OVER (
            PARTITION BY system, name
            ORDER BY version_ord
        ) AS previous_license
    FROM versions
)
WHERE previous_license IS NOT NULL
  AND lower(previous_license) <> lower(license)
ORDER BY system, name, version_ord
"""

PARQUET_SCHEMA = pa.schema(
    [
        ("system", pa.string()),
        ("name", pa.string()),
        ("version", pa.string()),
        ("previous_license", pa.string()),
        ("license", pa.string()),
    ]
)


def write_license_changes(snapshot_path: str | Path, output_path: str | Path) -> tuple[LicenseChange, ...]:
    changes = find_license_changes(version_rows(snapshot_path))
    write_changes(Path(output_path), changes)
    return changes


def version_rows(snapshot_path: str | Path) -> list[dict[str, object]]:
    path = Path(snapshot_path)
    payload = json.loads(path.read_text())
    packages = payload.get("packages") if isinstance(payload, dict) else None
    if isinstance(packages, list) and packages and _has_no_versions(payload, packages):
        raise SnapshotError("empty versions")
    return _ordered_rows(load_snapshot(path).packages)


def find_license_changes(rows: list[dict[str, object]]) -> tuple[LicenseChange, ...]:
    if not rows:
        return ()
    spark = session()
    frame = spark.createDataFrame(rows)
    frame.createOrReplaceTempView("versions")
    collected = spark.sql(CHANGE_SQL).collect()
    return tuple(
        LicenseChange(
            row.system,
            row.name,
            row.version,
            row.previous_license,
            row.license,
        )
        for row in collected
    )


def write_changes(path: Path, changes: tuple[LicenseChange, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {
        "system": [change.system for change in changes],
        "name": [change.name for change in changes],
        "version": [change.version for change in changes],
        "previous_license": [change.previous_license for change in changes],
        "license": [change.license for change in changes],
    }
    table = pa.table(columns, schema=PARQUET_SCHEMA).replace_schema_metadata({})
    pq.write_table(table, path, compression="snappy")


def _has_no_versions(payload: dict, packages: list) -> bool:
    if payload.get("versions") == []:
        return True
    return all(isinstance(row, dict) and "version" not in row for row in packages)


def _ordered_rows(packages: tuple[PackageVersion, ...]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[PackageVersion]] = {}
    for package in packages:
        grouped.setdefault((package.system, package.name), []).append(package)
    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        ordered = sorted(grouped[key], key=lambda package: Version(package.version))
        for ordinal, package in enumerate(ordered):
            rows.append(
                {
                    "system": package.system,
                    "name": package.name,
                    "version": package.version,
                    "license": package.license,
                    "version_ord": ordinal,
                }
            )
    return rows



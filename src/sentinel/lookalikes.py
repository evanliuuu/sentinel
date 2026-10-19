from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from sentinel.model import Lookalike, PackageVersion, load_snapshot
from sentinel.spark import session

DEFAULT_POPULAR_THRESHOLD = 1000

LOOKALIKE_SQL = """
SELECT
    system,
    name,
    version,
    popular_name,
    edit_distance,
    1.0 / (1 + edit_distance) AS score
FROM (
    SELECT
        n.system AS system,
        n.name AS name,
        n.version AS version,
        p.name AS popular_name,
        edit_distance(n.name, p.name) AS edit_distance
    FROM names n
    JOIN names p
      ON n.system = p.system
     AND n.initial = p.initial
     AND NOT n.popular
     AND p.popular
     AND n.name <> p.name
)
ORDER BY name, popular_name
"""

PARQUET_SCHEMA = pa.schema(
    [
        ("system", pa.string()),
        ("name", pa.string()),
        ("version", pa.string()),
        ("popular_name", pa.string()),
        ("edit_distance", pa.int32()),
        ("score", pa.float64()),
    ]
)


def write_lookalikes(
    snapshot_path: str | Path,
    output_path: str | Path,
    popular_threshold: int = DEFAULT_POPULAR_THRESHOLD,
) -> tuple[Lookalike, ...]:
    found = find_lookalikes(snapshot_path, popular_threshold)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "system": [row.system for row in found],
            "name": [row.name for row in found],
            "version": [row.version for row in found],
            "popular_name": [row.popular_name for row in found],
            "edit_distance": [row.edit_distance for row in found],
            "score": [1 / (1 + row.edit_distance) for row in found],
        },
        schema=PARQUET_SCHEMA,
    ).replace_schema_metadata({})
    pq.write_table(table, path, compression="snappy")
    return found


def find_lookalikes(
    snapshot_path: str | Path,
    popular_threshold: int = DEFAULT_POPULAR_THRESHOLD,
) -> tuple[Lookalike, ...]:
    rows = _name_rows(load_snapshot(snapshot_path).packages, popular_threshold)
    if not rows or not any(row["popular"] for row in rows):
        return ()
    if not any(not row["popular"] for row in rows):
        return ()
    spark = session()
    spark.udf.register("edit_distance", damerau_levenshtein)
    spark.createDataFrame(rows).createOrReplaceTempView("names")
    collected = spark.sql(LOOKALIKE_SQL).collect()
    return tuple(
        Lookalike(row.system, row.name, row.version, row.popular_name, int(row.edit_distance))
        for row in collected
    )


def damerau_levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    rows = len(left) + 1
    cols = len(right) + 1
    grid = [[0] * cols for _ in range(rows)]
    for index in range(rows):
        grid[index][0] = index
    for index in range(cols):
        grid[0][index] = index
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if left[i - 1] == right[j - 1] else 1
            grid[i][j] = min(
                grid[i - 1][j] + 1,
                grid[i][j - 1] + 1,
                grid[i - 1][j - 1] + cost,
            )
            if (
                i > 1
                and j > 1
                and left[i - 1] == right[j - 2]
                and left[i - 2] == right[j - 1]
            ):
                grid[i][j] = min(grid[i][j], grid[i - 2][j - 2] + 1)
    return grid[-1][-1]


def _name_rows(packages: tuple[PackageVersion, ...], threshold: int) -> list[dict[str, object]]:
    chosen: dict[tuple[str, str], PackageVersion] = {}
    for package in packages:
        key = (package.system, package.name)
        current = chosen.get(key)
        if current is None or package.dependent_count > current.dependent_count:
            chosen[key] = package
    return [
        {
            "system": package.system,
            "name": package.name,
            "version": package.version,
            "popular": package.dependent_count >= threshold,
            "initial": package.name[:1],
        }
        for package in chosen.values()
    ]

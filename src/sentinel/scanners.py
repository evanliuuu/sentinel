import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from sentinel.model import SnapshotError

SOURCES = ("deps.dev", "licensee", "package.json")
PARQUET_SCHEMA = pa.schema(
    [
        ("system", pa.string()),
        ("name", pa.string()),
        ("version", pa.string()),
        ("source", pa.string()),
        ("label", pa.string()),
        ("note", pa.string()),
    ]
)


def write_scan(
    changes_path: str | Path,
    output_path: str | Path,
    tarball_root: str | Path = "fixtures/tarballs",
) -> tuple[dict[str, str], ...]:
    changes = Path(changes_path)
    if not changes.exists():
        raise SnapshotError("missing license changes")
    rows = scan_rows(pq.read_table(changes).to_pylist(), Path(tarball_root))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {name: [row[name] for row in rows] for name in PARQUET_SCHEMA.names},
        schema=PARQUET_SCHEMA,
    ).replace_schema_metadata({})
    pq.write_table(table, path, compression="snappy")
    return rows


def scan_rows(changes: list[dict[str, str]], tarball_root: Path) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for change in changes:
        key = (change["name"], change["version"])
        seen.add(key)
        directory = tarball_root / f"{change['name']}-{change['version']}"
        rows.extend(
            _package_rows(change["system"], change["name"], change["version"], directory, change["license"])
        )
    if tarball_root.exists():
        for directory in sorted(path for path in tarball_root.iterdir() if path.is_dir()):
            name, version = _split_directory(directory.name)
            if (name, version) in seen:
                continue
            deps_file = directory / "deps.dev"
            if not deps_file.exists():
                continue
            rows.extend(
                _package_rows("NPM", name, version, directory, deps_file.read_text().strip())
            )
    return tuple(rows)


def _package_rows(
    system: str,
    name: str,
    version: str,
    directory: Path,
    deps_label: str,
) -> list[dict[str, str]]:
    if not directory.exists():
        return [_row(system, name, version, "tarball", "missing", "missing")]
    labels = {
        "deps.dev": deps_label,
        "licensee": _spdx((directory / "LICENSE").read_text()),
        "package.json": json.loads((directory / "package.json").read_text())["license"],
    }
    if labels["licensee"] == labels["deps.dev"]:
        note = "the LICENSE file was trusted"
    else:
        note = "unknown"
    return [_row(system, name, version, source, labels[source], note) for source in SOURCES]


def _row(system: str, name: str, version: str, source: str, label: str, note: str) -> dict[str, str]:
    return {
        "system": system,
        "name": name,
        "version": version,
        "source": source,
        "label": label,
        "note": note,
    }


def _spdx(text: str) -> str:
    for line in text.splitlines():
        marker = "SPDX-License-Identifier:"
        if marker in line:
            return line.split(marker, 1)[1].strip()
    stripped = text.strip()
    return stripped.splitlines()[0] if stripped else ""


def _split_directory(directory_name: str) -> tuple[str, str]:
    name, version = directory_name.rsplit("-", 1)
    return name, version

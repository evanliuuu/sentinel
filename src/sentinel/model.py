import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SnapshotError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Versioned:
    system: str
    name: str
    version: str

    @property
    def grain(self) -> tuple[str, str, str]:
        return (self.system, self.name, self.version)


@dataclass(frozen=True, slots=True)
class PackageVersion(Versioned):
    license: str
    dependent_count: int = 0


@dataclass(frozen=True, slots=True)
class LicenseChange(Versioned):
    previous_license: str
    license: str


@dataclass(frozen=True, slots=True)
class Lookalike(Versioned):
    popular_name: str
    edit_distance: int


@dataclass(frozen=True, slots=True)
class TeamPolicy(Versioned):
    team: str
    forbidden_licenses: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TenantExposure(Versioned):
    team: str
    root: str


@dataclass(frozen=True, slots=True)
class Dependency:
    system: str
    name: str
    version: str
    on_system: str
    on_name: str
    on_version: str


@dataclass(frozen=True, slots=True)
class Snapshot:
    packages: tuple[PackageVersion, ...]
    dependencies: tuple[Dependency, ...]
    policies: tuple[TeamPolicy, ...]


def load_snapshot(path: str | Path) -> Snapshot:
    payload = json.loads(Path(path).read_text())
    rows = payload.get("packages") if isinstance(payload, dict) else None
    if not rows:
        raise SnapshotError("empty snapshot")
    packages = _packages(rows)
    by_grain = {package.grain: package for package in packages}
    return Snapshot(
        packages,
        _dependencies(payload.get("dependencies") or [], by_grain),
        _policies(payload.get("teams") or [], by_grain),
    )


def _packages(rows: list[dict[str, Any]]) -> tuple[PackageVersion, ...]:
    packages: list[PackageVersion] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        grain = _grain(row)
        license_name = row.get("license")
        if not isinstance(license_name, str) or license_name.strip() == "":
            raise SnapshotError(f"missing license {_label(grain)}")
        if grain in seen:
            raise SnapshotError(f"duplicate grain {_label(grain)}")
        seen.add(grain)
        packages.append(
            PackageVersion(*grain, license_name.strip(), int(row.get("dependent_count") or 0))
        )
    return tuple(packages)


def _dependencies(
    rows: list[dict[str, Any]],
    packages: dict[tuple[str, str, str], PackageVersion],
) -> tuple[Dependency, ...]:
    edges: list[Dependency] = []
    for row in rows:
        grain = _grain(row)
        on_grain = _grain(row["depends_on"])
        if grain not in packages or on_grain not in packages:
            missing = on_grain if on_grain not in packages else grain
            raise SnapshotError(f"missing package {_label(missing)}")
        edges.append(Dependency(*grain, *on_grain))
    return tuple(edges)


def _policies(
    teams: list[dict[str, Any]],
    packages: dict[tuple[str, str, str], PackageVersion],
) -> tuple[TeamPolicy, ...]:
    policies: list[TeamPolicy] = []
    seen: set[tuple[str, str, str]] = set()
    for team_row in teams:
        forbidden = tuple(team_row.get("forbidden_licenses") or ())
        for root in team_row["roots"]:
            grain = _grain(root)
            if grain in seen:
                raise SnapshotError(f"duplicate grain {_label(grain)}")
            if grain not in packages:
                raise SnapshotError(f"missing package {_label(grain)}")
            seen.add(grain)
            policies.append(TeamPolicy(*grain, team_row["team"], forbidden))
    return tuple(policies)


def _grain(row: dict[str, Any]) -> tuple[str, str, str]:
    return (row["system"], row["name"], row["version"])


def _label(grain: tuple[str, str, str]) -> str:
    return " ".join(grain)

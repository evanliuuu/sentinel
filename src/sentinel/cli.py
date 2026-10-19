import argparse
from collections.abc import Callable

from sentinel.license_changes import write_license_changes
from sentinel.lookalikes import DEFAULT_POPULAR_THRESHOLD, write_lookalikes
from sentinel.model import Snapshot, SnapshotError, load_snapshot
from sentinel.scanners import write_scan


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = _COMMANDS.get(args.command)
    if command is None:
        raise AssertionError(args.command)
    try:
        return command(args)
    except SnapshotError as error:
        print(error)
        return 1


def _fixture(args: argparse.Namespace) -> int:
    print(render(load_snapshot(args.snapshot), args.team), end="")
    return 0


def _licenses(args: argparse.Namespace) -> int:
    for change in write_license_changes(args.snapshot, args.output):
        print(
            f"{change.name} {change.version} previous {change.previous_license} license {change.license}"
        )
    return 0


def _squats(args: argparse.Namespace) -> int:
    for row in write_lookalikes(args.snapshot, args.output, args.popular_threshold):
        print(f"{row.name} {row.popular_name} distance {row.edit_distance}")
    return 0


def _scan(args: argparse.Namespace) -> int:
    for row in write_scan(args.changes, args.output, args.tarballs):
        print(f"{row['name']} {row['source']} {row['label']} {row['note']}")
    return 0


_COMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {
    "fixture": _fixture,
    "licenses": _licenses,
    "squats": _squats,
    "scan": _scan,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinel")
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("--snapshot", default="fixtures/snapshot.json")
    fixture.add_argument("--team")
    licenses = commands.add_parser("licenses")
    licenses.add_argument("--snapshot", default="fixtures/snapshot.json")
    licenses.add_argument("--output", default="out/license_change.parquet")
    squats = commands.add_parser("squats")
    squats.add_argument("--snapshot", default="fixtures/snapshot.json")
    squats.add_argument("--output", default="out/lookalikes.parquet")
    squats.add_argument("--popular-threshold", type=int, default=DEFAULT_POPULAR_THRESHOLD)
    scan = commands.add_parser("scan")
    scan.add_argument("--changes", default="out/license_change.parquet")
    scan.add_argument("--tarballs", default="fixtures/tarballs")
    scan.add_argument("--output", default="out/scanner_disagreement.parquet")
    return parser


def render(snapshot: Snapshot, team: str | None) -> str:
    if team is None:
        return _render_all(snapshot)
    policies = tuple(row for row in snapshot.policies if row.team == team)
    if not policies:
        raise SnapshotError(f"unknown team {team}")
    lines = [
        f"{policy.team} root {policy.name}"
        for policy in sorted(policies, key=lambda row: (row.team, row.grain))
    ]
    return "\n".join(lines) + "\n"


def _render_all(snapshot: Snapshot) -> str:
    lines = [
        f"{package.name} {package.version} license {package.license}"
        for package in sorted(snapshot.packages, key=lambda row: row.grain)
    ]
    seen: set[tuple[str, str]] = set()
    ordered = sorted(
        snapshot.dependencies,
        key=lambda row: (row.name, row.on_name, row.version, row.on_version),
    )
    for edge in ordered:
        pair = (edge.name, edge.on_name)
        if pair in seen:
            continue
        seen.add(pair)
        lines.append(f"{edge.name} depends on {edge.on_name}")
    for policy in sorted(snapshot.policies, key=lambda row: (row.team, row.grain)):
        lines.append(f"{policy.team} root {policy.name}")
    return "\n".join(lines) + "\n"

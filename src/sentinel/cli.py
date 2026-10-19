import argparse

from sentinel.model import Snapshot, SnapshotError, load_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sentinel")
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("--snapshot", default="fixtures/snapshot.json")
    fixture.add_argument("--team")
    args = parser.parse_args(argv)
    if args.command != "fixture":
        raise AssertionError(args.command)
    try:
        text = render(load_snapshot(args.snapshot), args.team)
    except SnapshotError as error:
        print(error)
        return 1
    print(text, end="")
    return 0


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

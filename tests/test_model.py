from pathlib import Path

import pytest

from sentinel.cli import main
from sentinel.model import (
    LicenseChange,
    Lookalike,
    SnapshotError,
    TenantExposure,
    load_snapshot,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SNAPSHOT = FIXTURES / "snapshot.json"


def test_grain_is_system_name_and_version():
    snapshot = load_snapshot(SNAPSHOT)
    widget = next(
        package
        for package in snapshot.packages
        if package.name == "widget" and package.version == "2.0.0"
    )
    previous = next(
        package
        for package in snapshot.packages
        if package.name == "widget" and package.version == "1.0.0"
    )
    raect = next(package for package in snapshot.packages if package.name == "raect")
    alpha = next(policy for policy in snapshot.policies if policy.team == "alpha")
    change = LicenseChange(
        widget.system,
        widget.name,
        widget.version,
        previous.license,
        widget.license,
    )
    lookalike = Lookalike(raect.system, raect.name, raect.version, "react", 1)
    exposure = TenantExposure(widget.system, widget.name, widget.version, "alpha", alpha.name)
    rows = (widget, change, lookalike, alpha, exposure)
    assert all(row.grain == (row.system, row.name, row.version) for row in rows)
    grains = [package.grain for package in snapshot.packages]
    assert len(grains) == len(set(grains))


def test_widget_license_pair():
    snapshot = load_snapshot(SNAPSHOT)
    licenses = {
        package.version: package.license
        for package in snapshot.packages
        if package.name == "widget"
    }
    assert licenses == {"1.0.0": "MIT", "2.0.0": "SSPL"}
    change = LicenseChange("NPM", "widget", "2.0.0", "MIT", "SSPL")
    assert change.previous_license == "MIT"
    assert change.license == "SSPL"
    assert change.grain == ("NPM", "widget", "2.0.0")


def test_raect_and_react_pair():
    snapshot = load_snapshot(SNAPSHOT)
    react = next(package for package in snapshot.packages if package.name == "react")
    raect = next(package for package in snapshot.packages if package.name == "raect")
    assert react.dependent_count > raect.dependent_count
    assert _one_adjacent_swap(react.name, raect.name)
    lookalike = Lookalike(raect.system, raect.name, raect.version, react.name, 1)
    assert lookalike.popular_name == "react"
    assert lookalike.edit_distance == 1
    assert lookalike.grain == (raect.system, raect.name, raect.version)


def test_team_roots():
    snapshot = load_snapshot(SNAPSHOT)
    by_team = {policy.team: policy for policy in snapshot.policies}
    assert by_team["alpha"].name == "app-a"
    assert by_team["alpha"].grain == ("NPM", "app-a", "1.0.0")
    assert "SSPL" in by_team["alpha"].forbidden_licenses
    assert by_team["beta"].name == "app-b"
    assert by_team["beta"].grain == ("NPM", "app-b", "1.0.0")
    assert "SSPL" not in by_team["beta"].forbidden_licenses


def test_duplicate_grain():
    with pytest.raises(SnapshotError, match="duplicate grain"):
        load_snapshot(FIXTURES / "bad-duplicate.json")


def test_missing_license():
    with pytest.raises(SnapshotError, match="missing license"):
        load_snapshot(FIXTURES / "bad-license.json")


def test_empty_snapshot():
    with pytest.raises(SnapshotError, match="empty snapshot"):
        load_snapshot(FIXTURES / "empty.json")


def test_fixture_print(capsys: pytest.CaptureFixture[str]):
    assert main(["fixture", "--snapshot", str(SNAPSHOT)]) == 0
    first = capsys.readouterr().out
    assert "widget 2.0.0 license SSPL" in first
    assert "left-pad 1.0.0 license MIT" in first
    assert "left-pad 1.1.0 license MIT" in first
    assert "react" in first
    assert "raect" in first
    assert "app-a depends on widget" in first
    assert "app-b depends on left-pad" in first
    assert "alpha root app-a" in first
    assert "beta root app-b" in first
    assert main(["fixture", "--snapshot", str(SNAPSHOT)]) == 0
    assert capsys.readouterr().out == first


def test_fixture_team_alpha(capsys: pytest.CaptureFixture[str]):
    assert main(["fixture", "--snapshot", str(SNAPSHOT), "--team", "alpha"]) == 0
    output = capsys.readouterr().out
    assert output == "alpha root app-a\n"
    assert "app-b" not in output


def test_fixture_team_beta(capsys: pytest.CaptureFixture[str]):
    assert main(["fixture", "--snapshot", str(SNAPSHOT), "--team", "beta"]) == 0
    output = capsys.readouterr().out
    assert output == "beta root app-b\n"
    assert "app-a" not in output


def test_fixture_rejects_bad_snapshots(capsys: pytest.CaptureFixture[str]):
    cases = (
        ("bad-duplicate.json", "duplicate grain"),
        ("bad-license.json", "missing license"),
        ("empty.json", "empty snapshot"),
    )
    for name, phrase in cases:
        code = main(["fixture", "--snapshot", str(FIXTURES / name)])
        assert code != 0
        assert phrase in capsys.readouterr().out


def _one_adjacent_swap(left: str, right: str) -> bool:
    if len(left) != len(right):
        return False
    diffs = [index for index, pair in enumerate(zip(left, right)) if pair[0] != pair[1]]
    if len(diffs) != 2:
        return False
    first, second = diffs
    return second == first + 1 and left[first] == right[second] and left[second] == right[first]

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOMMENDATION = ROOT / "docs/recommendation.md"
SENTINEL = ROOT / ".venv/bin/sentinel"


def main() -> int:
    recommendation = RECOMMENDATION.read_text()
    inherited = _ask("alpha", "inherited")
    lookalikes = _ask("alpha", "lookalikes")
    allowed = _names(inherited + "\n" + lookalikes)
    allowed.update(_names(_scan()))
    cited = set(re.findall(r"`([^`]+)`", recommendation))
    unknown = sorted(name for name in cited if name not in allowed)
    if unknown:
        print("recommendation names a package ask did not return: " + ", ".join(unknown))
        return 1
    row_ids = re.findall(r"^row_id: .+$", inherited, flags=re.M)
    allowed_counts = {str(len(row_ids))}
    allowed_counts.update(re.findall(r"\b\d+\b", inherited))
    for count in re.findall(r"\b\d+\b", recommendation):
        if count not in allowed_counts:
            print(f"recommendation names a count ask did not return: {count}")
            return 1
    if "unknown" not in recommendation.lower():
        print("recommendation does not name the unknown scanner case")
        return 1
    print("recommendation matches ask")
    return 0


def _ask(team: str, question: str) -> str:
    return subprocess.check_output(
        [str(SENTINEL), "ask", "--team", team, "--question", question],
        cwd=ROOT,
        text=True,
    )


def _scan() -> str:
    return subprocess.check_output([str(SENTINEL), "scan"], cwd=ROOT, text=True)


def _names(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9][A-Za-z0-9.-]*", text))


if __name__ == "__main__":
    sys.exit(main())

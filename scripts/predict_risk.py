import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILES = {"requirements.txt", "pytest.ini", ".github/workflows/ci.yml"}


def numstat(base, head):
    out = subprocess.run(
        ["git", "diff", "--numstat", base, head],
        capture_output=True, text=True, check=True, cwd=ROOT,
    ).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added, removed, path = parts
            churn = (int(added) if added.isdigit() else 0) + (int(removed) if removed.isdigit() else 0)
            rows.append((path, churn))
    return rows


def score(rows):
    total = 0
    reasons = []
    for path, churn in rows:
        if path in CONFIG_FILES:
            total += 30
            reasons.append(f"{path} changed (+30)")
        elif path.startswith("src/") and path.endswith(".py"):
            points = 5 + min(churn, 50) // 5
            total += points
            reasons.append(f"{path} changed by {churn} lines (+{points})")
        elif path.startswith("tests/"):
            total += 2
            reasons.append(f"{path} changed (+2)")
    if total >= 30:
        level = "high"
    elif total >= 10:
        level = "medium"
    else:
        level = "low"
    return total, level, reasons


if __name__ == "__main__":
    base, head = sys.argv[1], sys.argv[2]
    rows = numstat(base, head)
    total, level, reasons = score(rows)
    report = {"base": base, "head": head, "score": total, "level": level, "reasons": reasons}
    print(json.dumps(report, indent=2))
    Path("risk-report.json").write_text(json.dumps(report, indent=2))
    if level == "high":
        print(f"::warning::Build-failure risk is {level} (score {total})")

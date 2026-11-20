import sys
from pathlib import Path

def summarize(log_text):
    lines = log_text.splitlines()
    failed = [l for l in lines if l.startswith("FAILED")]
    errors = [l.strip() for l in lines if l.startswith("E ")]

    if not failed and not errors:
        return "Build passed. No failures found in the log."

    out = ["# Build summary", "", f"{len(failed)} test(s) failed:"]
    for f in failed:
        out.append(f"- {f}")
    if errors:
        out.append("")
        out.append("Key error lines:")
        for e in errors[:10]:
            out.append(f"- {e}")
    out.append("")
    out.append("Suggested next step: open the failing test, compare its expected value with what the code returns, and fix whichever one is wrong.")
    return "\n".join(out)

if __name__ == "__main__":
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build.log")
    if not log_path.exists():
        print(f"No log file found at {log_path}")
        sys.exit(0)
    summary = summarize(log_path.read_text())
    Path("build-summary.md").write_text(summary + "\n")
    print(summary)

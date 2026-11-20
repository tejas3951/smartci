import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_ALL = {"requirements.txt", "pytest.ini", ".github/workflows/ci.yml"}


def changed_files(base, head):
    out = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        capture_output=True, text=True, check=True, cwd=ROOT,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def module_imports(name):
    text = (ROOT / "src" / f"{name}.py").read_text()
    return set(re.findall(r"^from src\.(\w+) import", text, re.M))


def affected_modules(changed, deps):
    result = set(changed)
    grew = True
    while grew:
        grew = False
        for mod, imports in deps.items():
            if mod not in result and imports & result:
                result.add(mod)
                grew = True
    return result


def main():
    base, head = sys.argv[1], sys.argv[2]
    files = changed_files(base, head)
    all_tests = sorted(f"tests/{p.name}" for p in (ROOT / "tests").glob("test_*.py"))

    if not files or any(f in RUN_ALL for f in files):
        print(" ".join(all_tests))
        return

    modules = [p.stem for p in (ROOT / "src").glob("*.py") if p.stem != "__init__"]
    deps = {m: module_imports(m) for m in modules}

    changed_modules = set()
    selected = set()
    for f in files:
        if f.startswith("src/") and f.endswith(".py"):
            changed_modules.add(Path(f).stem)
        elif f.startswith("tests/") and f.endswith(".py"):
            selected.add(f)

    for mod in affected_modules(changed_modules, deps):
        selected.add(f"tests/test_{mod}.py")

    existing = set(all_tests)
    print(" ".join(sorted(t for t in selected if t in existing)))


if __name__ == "__main__":
    main()
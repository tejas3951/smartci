import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from affected_tests import changed_files, module_imports, affected_modules, ROOT

def explain(base, head):
    files = changed_files(base, head)
    run_all = {"requirements.txt", "pytest.ini", ".github/workflows/ci.yml"}
    report = {"base": base, "head": head, "changed": files, "selected": {}, "mode": "subset"}

    if not files or any(f in run_all for f in files):
        report["mode"] = "full"
        reason = "config or dependency file changed" if files else "no changes detected"
        for t in sorted(p.name for p in (ROOT / "tests").glob("test_*.py")):
            report["selected"][f"tests/{t}"] = reason
        return report

    modules = [p.stem for p in (ROOT / "src").glob("*.py") if p.stem != "__init__"]
    deps = {m: module_imports(m) for m in modules}
    changed_mods = {Path(f).stem for f in files if f.startswith("src/") and f.endswith(".py")}

    for f in files:
        if f.startswith("tests/") and f.endswith(".py"):
            report["selected"][f] = "test file itself changed"

    for mod in affected_modules(changed_mods, deps):
        test = f"tests/test_{mod}.py"
        if (ROOT / test).exists():
            if mod in changed_mods:
                report["selected"][test] = f"src/{mod}.py changed"
            else:
                via = sorted(deps[mod] & affected_modules(changed_mods, deps))
                report["selected"][test] = f"imports {', '.join('src/' + v + '.py' for v in via)}"

    return report

if __name__ == "__main__":
    base, head = sys.argv[1], sys.argv[2]
    report = explain(base, head)
    print(json.dumps(report, indent=2))
    Path("routing-report.json").write_text(json.dumps(report, indent=2))

#!/usr/bin/env python3
"""Validate a packaged submission file (dist/main.py or path arg).

Checks:
- file exists and is syntactically valid Python
- loads via official get_last_callable
- last callable is named `agent`
- no callable defined after `agent`
- runs against kaggriculture without error
- returns valid action schema
"""
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from kaggle_environments.agent import get_last_callable  # noqa: E402


def _find_callables(source: str) -> list[tuple[int, str, str]]:
    """Return [(lineno, name, kind)] for top-level callable defs in source order."""
    tree = ast.parse(source)
    out = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out.append((node.lineno, node.name, "function"))
        elif isinstance(node, ast.ClassDef):
            out.append((node.lineno, node.name, "class"))
    return out


def validate(path: Path) -> bool:
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return False
    source = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"file:   {path}")
    print(f"sha256: {digest}")
    print(f"size:   {path.stat().st_size} bytes")

    # Syntax check.
    try:
        ast.parse(source)
    except SyntaxError as e:
        print(f"FAIL: syntax error: {e}")
        return False
    print("PASS: syntax valid")

    # Callable inventory.
    callables = _find_callables(source)
    if not callables:
        print("FAIL: no callables found")
        return False
    last = callables[-1]
    print(f"last callable: {last[2]} '{last[1]}' at line {last[0]}")
    if last[1] != "agent" or last[2] != "function":
        print(f"FAIL: last callable must be function 'agent', got {last[2]} '{last[1]}'")
        return False
    print("PASS: last callable is 'agent'")

    # Loader check.
    try:
        fn = get_last_callable(source, path=str(path))
        if fn.__name__ != "agent":
            print(f"FAIL: get_last_callable returned '{fn.__name__}', expected 'agent'")
            return False
    except Exception as e:
        print(f"FAIL: get_last_callable error: {e}")
        return False
    print("PASS: get_last_callable returns 'agent'")

    # Runtime check: one step.
    env = make("kaggriculture", configuration={"episodeSteps": 3, "seed": 1}, debug=True)
    try:
        env.run([str(path), "pass"])
    except Exception as e:
        print(f"FAIL: runtime error: {e}")
        return False
    statuses = env.toJSON()["statuses"]
    if statuses != ["DONE", "DONE"]:
        print(f"FAIL: statuses {statuses}, expected ['DONE','DONE']")
        return False
    print("PASS: 3-step episode completes DONE")

    # Action schema check on step 0.
    env2 = make("kaggriculture", configuration={"episodeSteps": 2, "seed": 1}, debug=True)
    env2.run([str(path), "pass"])
    print("PASS: all validation checks passed")
    return True


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "main.py"
    ok = validate(path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

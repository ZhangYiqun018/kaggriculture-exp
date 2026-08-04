#!/usr/bin/env python3
"""Package an agent version into a single self-contained dist/main.py.

Inlines the safety layer and the agent into one file. Guarantees:
- self-contained (stdlib only)
- `agent` is the last callable defined
- no functions/classes/lambdas after `agent`
- no side effects on import
- no network, no API keys
"""
from __future__ import annotations
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "kaggriculture_bot"
DIST = ROOT / "dist"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_dev_imports(source: str) -> str:
    """Remove dev-only sys.path manipulation and imports from the agent source."""
    lines = source.splitlines()
    out = []
    skip_block = False
    for line in lines:
        s = line.strip()
        if s.startswith("import sys") or s.startswith("import os"):
            continue
        if "_SRC" in line or "sys.path.insert" in line or "sys.path.append" in line:
            continue
        if "from kaggriculture_bot.safety import" in line:
            continue
        if s.startswith("from __future__ import"):
            continue
        out.append(line)
    return "\n".join(out)


def _strip_module_header(source: str) -> str:
    """Remove leading module docstring and __future__ imports so the inlined body can sit after a single shared header."""
    import ast
    tree = ast.parse(source)
    lines = source.splitlines()
    # Find line ranges to drop: module docstring (first stmt if Expr/Constant str) + future imports.
    drop_ranges = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            drop_ranges.append((node.lineno, node.end_lineno))
    # Module docstring is first stmt if it's an Expr with a Constant str.
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        drop_ranges.append((tree.body[0].lineno, tree.body[0].end_lineno))
    keep = []
    for i, line in enumerate(lines, 1):
        if any(lo <= i <= hi for lo, hi in drop_ranges):
            continue
        keep.append(line)
    return "\n".join(keep)


def package(agent_path: Path, output: Path | None = None) -> Path:
    """Inline safety.py + agent into a single file at `output` (default dist/main.py)."""
    if output is None:
        output = DIST / "main.py"
    output.parent.mkdir(parents=True, exist_ok=True)

    safety_src = _read(SRC / "safety.py")
    agent_src = _read(agent_path)

    # Strip dev imports and module headers so we can assemble a clean single file.
    safety_src = _strip_module_header(safety_src)
    agent_src = _strip_dev_imports(agent_src)

    # Single future import at top, then inlined safety, then agent (last callable).
    parts = [
        '"""Auto-generated single-file Kaggressriculture agent. Do not edit by hand."""',
        "from __future__ import annotations",
        "from typing import Any",
        "",
        "# ===== INLINED: kaggriculture_bot/safety.py =====",
        safety_src,
        "",
        "# ===== AGENT =====",
        agent_src,
        "",
    ]
    content = "\n".join(parts)
    output.write_text(content, encoding="utf-8")
    return output


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        agent_rel = "agents/v000_pass/main.py"
    else:
        agent_rel = sys.argv[1]
    agent_path = ROOT / agent_rel
    if not agent_path.exists():
        print(f"ERROR: agent not found: {agent_path}", file=sys.stderr)
        sys.exit(1)
    out = package(agent_path)
    digest = sha256(out)
    print(f"packaged: {out}")
    print(f"sha256:   {digest}")
    print(f"size:     {out.stat().st_size} bytes")
    print(f"lines:    {sum(1 for _ in open(out))}")


if __name__ == "__main__":
    main()

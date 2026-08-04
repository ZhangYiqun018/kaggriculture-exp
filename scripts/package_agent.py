#!/usr/bin/env python3
"""Package an agent version into a single self-contained dist file.

Inlines the kaggriculture_bot modules the agent depends on, in dependency
order (constants -> safety -> state -> economy), strips their module headers
and intra-package imports, then appends the agent (whose `agent` function must
be the last callable in the file).

Usage:
    python scripts/package_agent.py agents/v000_pass/main.py [output_path]
"""
from __future__ import annotations
import ast
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "kaggriculture_bot"

# Fixed inline order: any module may only NAME dependencies on earlier ones.
INLINE_MODULES = ["constants.py", "safety.py", "state.py", "economy.py",
                  "tasks.py", "assignment.py", "hire_manager.py"]

# Per-file import lines that must be dropped when inlining (they are hoisted to
# the top of the bundle or already provided by earlier inlined modules).
STRIP_PREFIXES = (
    "from __future__ import",
    "from typing import",
    "from dataclasses import",
    "import math",
    "import sys",
    "import os",
    "from .constants import",
    "from .safety import",
    "from .state import",
    "from .economy import",
    "from .tasks import",
    "from .assignment import",
    "from .hire_manager import",
    "from kaggriculture_bot",
    "from kaggriculture_bot.",
)

HOISTED_HEADER = '''"""Auto-generated single-file Kaggressriculture agent. Do not edit by hand."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import math
'''


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_module_docstring(source: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines()
    drop = []
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        drop.append((tree.body[0].lineno, tree.body[0].end_lineno))
    return "\n".join(line for i, line in enumerate(lines, 1) if not any(lo <= i <= hi for lo, hi in drop))


def _strip_lines(source: str, extra_prefixes: tuple[str, ...] = ()) -> str:
    prefixes = STRIP_PREFIXES + extra_prefixes
    out = []
    skip_parens = False
    for line in source.splitlines():
        s = line.strip()
        if skip_parens:
            if s.endswith(")") or s == ")":
                skip_parens = False
            continue
        if "_SRC" in line or "sys.path.insert" in line or "sys.path.append" in line:
            continue
        if any(s.startswith(p) for p in prefixes):
            # Parenthesized multi-line import: skip until closing ")".
            if "(" in s and not s.rstrip().endswith(")"):
                skip_parens = True
            continue
        out.append(line)
    return "\n".join(out)


def package(agent_path: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    parts = [HOISTED_HEADER]
    for mod in INLINE_MODULES:
        body = _strip_module_docstring(_read(SRC / mod))
        body = _strip_lines(body)
        parts.append(f"\n# ===== INLINED: kaggriculture_bot/{mod} =====\n")
        parts.append(body)
    agent_src = _strip_lines(_strip_module_docstring(_read(agent_path)),
                             extra_prefixes=())
    parts.append("\n# ===== AGENT =====\n")
    parts.append(agent_src)
    parts.append("")
    output.write_text("\n".join(parts), encoding="utf-8")
    return output


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        agent_rel = "agents/v000_pass/main.py"
        out_rel = "dist/main.py"
    else:
        agent_rel = sys.argv[1]
        # dist/<version>/main.py mirroring agents/<version>/main.py
        version = Path(agent_rel).parent.name
        out_rel = f"dist/{version}/main.py"
    out_or_override = sys.argv[2] if len(sys.argv) > 2 else out_rel
    agent_path = ROOT / agent_rel
    if not agent_path.exists():
        print(f"ERROR: agent not found: {agent_path}", file=sys.stderr)
        sys.exit(1)
    out = package(agent_path, ROOT / out_or_override)
    digest = sha256(out)
    print(f"packaged: {out}")
    print(f"sha256:   {digest}")
    print(f"size:     {out.stat().st_size} bytes")
    print(f"lines:    {sum(1 for _ in open(out))}")


if __name__ == "__main__":
    main()

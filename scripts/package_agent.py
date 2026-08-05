#!/usr/bin/env python3
"""Package an agent version into a single self-contained dist file.

CANONICAL PIPELINE (Phase 3R.1):
    python scripts/package_agent.py            -> agents/champion/main.py -> dist/main.py
    python scripts/package_agent.py --agent X  -> X -> dist/<version>/main.py
    python scripts/package_agent.py --agent X --output dist/main.py

Every package writes manifest.json next to the artifact with full provenance:
    agent_version, source_path, git_sha, source_sha256, artifact_sha256,
    environment_name, environment_version.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Package dir discovered from disk (never a literal, to avoid spelling traps).
SRC = None
for c in (ROOT / "src").iterdir():
    if c.is_dir() and c.name.startswith("kagg"):
        SRC = c
        break
_DIR_NAME = SRC.name

INLINE_MODULES = ["constants.py", "safety.py", "state.py", "economy.py", "crop_allocator.py",
                  "tasks.py", "assignment.py", "hire_manager.py", "policy.py", "harness.py"]

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
    "from .crop_allocator import",
    "from .tasks import",
    "from .assignment import",
    "from .hire_manager import",
    "from .policy import",
    "from .harness import",
    f"from {_DIR_NAME}",
    f"from {_DIR_NAME}.",
)

HOISTED_HEADER = '''"""Auto-generated single-file agent. Do not edit by hand."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import math
import os
import traceback
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


def _strip_lines(source: str, extra_prefixes=()):
    prefixes = tuple(STRIP_PREFIXES) + tuple(extra_prefixes)
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
        parts.append(f"\n# ===== INLINED: {_DIR_NAME}/{mod} =====\n")
        parts.append(body)
    agent_src = _strip_lines(_strip_module_docstring(_read(agent_path)))
    parts.append("\n# ===== AGENT =====\n")
    parts.append(agent_src)
    parts.append("")
    output.write_text("\n".join(parts), encoding="utf-8")
    return output


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "UNKNOWN"


def _env_version() -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version("kaggle-environments")
    except Exception:
        return "UNKNOWN"


def write_manifest(agent_path: Path, output: Path, agent_version: str) -> Path:
    manifest = {
        "agent_version": agent_version,
        "source_path": str(agent_path.relative_to(ROOT)),
        "git_sha": _git_sha(),
        "source_sha256": sha256(agent_path),
        "artifact_sha256": sha256(output),
        "artifact_path": str(output.relative_to(ROOT)),
        "environment_name": "kaggriculture",
        "environment_version": _env_version(),
    }
    mp = output.parent / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="agents/champion/main.py")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    agent_path = ROOT / args.agent
    if not agent_path.exists():
        print(f"ERROR: agent not found: {agent_path}", file=sys.stderr)
        sys.exit(1)
    out_rel = args.output or "dist/main.py"
    output = ROOT / out_rel
    agent_version = agent_path.parent.name
    out = package(agent_path, output)
    mp = write_manifest(agent_path, out, agent_version)
    print(f"packaged: {out}")
    print(f"manifest: {mp}")
    print(f"agent:    {agent_version}")
    print(f"sha256:   {sha256(out)}")
    print(f"size:     {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()

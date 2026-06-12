"""Audit tracked repository files against project hygiene rules.

The script is intentionally read-only. It checks files already tracked by Git
and exits with a non-zero status when forbidden paths or file types are found.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    description: str


RULES = [
    Rule(
        name="legacy-top-level-directory",
        pattern=re.compile(r"^(Manage|Back|python|GasModelTest|img)/"),
        description="old top-level directory name",
    ),
    Rule(
        name="dependency-or-build-output",
        pattern=re.compile(r"(^|/)(node_modules|__pycache__|\.venv|target|dist|build)(/|$)"),
        description="dependency cache or build output",
    ),
    Rule(
        name="compiled-or-cache-file",
        pattern=re.compile(r"\.(pyc|pyo|class|log|tmp|temp|bak|swp)$", re.IGNORECASE),
        description="compiled, log, backup, or temporary file",
    ),
    Rule(
        name="model-or-generated-array",
        pattern=re.compile(r"\.(pt|pth|onnx|npy|npz)$", re.IGNORECASE),
        description="model weight or generated numerical array",
    ),
    Rule(
        name="environment-or-secret-file",
        pattern=re.compile(r"(^|/)(\.env|\.env\..*\.local|.*\.pem|.*\.key|.*\.p12)$", re.IGNORECASE),
        description="environment or secret-bearing file",
    ),
    Rule(
        name="stale-entrypoint-artifact",
        pattern=re.compile(r"(^|/)(apiServer\.py|.*\.spec|pnpm-lock\.yaml|vite\.svg)$"),
        description="stale generated or duplicate entrypoint artifact",
    ),
]


def tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    violations: list[tuple[str, Rule]] = []

    for path in tracked_files(repo_root):
        for rule in RULES:
            if rule.pattern.search(path):
                violations.append((path, rule))

    if not violations:
        print("Repository tracked-file audit passed.")
        return 0

    print("Repository tracked-file audit failed:")
    for path, rule in violations:
        print(f"- [{rule.name}] {path} ({rule.description})")
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Audit source files for avoidable duplicate or meaningless definitions.

This script is intentionally conservative and read-only. It does not try to
replace language-specific linters. Instead, it enforces a small set of project
rules that are cheap to verify before code is pushed:

- no duplicate top-level declarations in the same source file;
- no obviously meaningless top-level symbol names;
- Python source module names in maintained code folders use snake_case.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SOURCE_PREFIXES = (
    "algorithm/",
    "backend/src/main/java/",
    "frontend/src/",
    "scripts/",
    "tests/",
    "tools/",
)

SOURCE_SUFFIXES = (".py", ".ts", ".js", ".vue", ".java")

PYTHON_PREFIXES = ("algorithm/", "scripts/", "tests/", "tools/")

MEANINGLESS_NAMES = {
    "aaa",
    "bbb",
    "ccc",
    "demo",
    "foo",
    "bar",
    "baz",
    "temp",
    "tmp",
    "xxx",
    "yyy",
    "zzz",
}

SNAKE_CASE_MODULE = re.compile(r"^[a-z][a-z0-9_]*\.py$")
STANDARD_PYTHON_MODULES = {"__init__.py"}
VUE_SCRIPT_BLOCK = re.compile(
    r"<script\b[^>]*>(?P<body>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)

DECLARATION_PATTERNS = {
    ".py": re.compile(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE),
    ".ts": re.compile(
        r"^(?:export\s+)?(?:const|let|var|function|class|interface|type)\s+([A-Za-z_$][A-Za-z0-9_$]*)\b",
        re.MULTILINE,
    ),
    ".js": re.compile(
        r"^(?:export\s+)?(?:const|let|var|function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)\b",
        re.MULTILINE,
    ),
    ".vue": re.compile(
        r"^(?:const|let|var|function|class|interface|type)\s+([A-Za-z_$][A-Za-z0-9_$]*)\b",
        re.MULTILINE,
    ),
    ".java": re.compile(
        r"^(?:public\s+)?(?:abstract\s+)?(?:final\s+)?(?:class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        re.MULTILINE,
    ),
}


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    detail: str


def tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode("utf-8", errors="replace").split("\0")
    return [path.replace("\\", "/") for path in paths if path]


def is_source_file(path: str) -> bool:
    return path.startswith(SOURCE_PREFIXES) and path.endswith(SOURCE_SUFFIXES)


def source_text(repo_root: Path, path: str) -> str:
    text = (repo_root / path).read_text(encoding="utf-8", errors="replace")
    if path.endswith(".vue"):
        blocks = [match.group("body") for match in VUE_SCRIPT_BLOCK.finditer(text)]
        return "\n".join(blocks)
    return text


def declaration_names(path: str, text: str) -> list[str]:
    suffix = Path(path).suffix
    pattern = DECLARATION_PATTERNS.get(suffix)
    if pattern is None:
        return []
    return [match.group(1) for match in pattern.finditer(text)]


def check_duplicate_declarations(path: str, names: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for name, count in Counter(names).items():
        if count > 1:
            findings.append(
                Finding(
                    path=path,
                    rule="duplicate-top-level-declaration",
                    detail=f"{name!r} is declared {count} times in the same file",
                )
            )
    return findings


def check_meaningless_names(path: str, names: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for name in names:
        if name.lower() in MEANINGLESS_NAMES:
            findings.append(
                Finding(
                    path=path,
                    rule="meaningless-top-level-name",
                    detail=f"{name!r} is too vague for a maintained top-level symbol",
                )
            )
    return findings


def check_python_module_name(path: str) -> list[Finding]:
    if not path.startswith(PYTHON_PREFIXES) or not path.endswith(".py"):
        return []
    filename = Path(path).name
    if filename in STANDARD_PYTHON_MODULES:
        return []
    if SNAKE_CASE_MODULE.match(filename):
        return []
    return [
        Finding(
            path=path,
            rule="python-module-name",
            detail="Python module names must use snake_case",
        )
    ]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    findings: list[Finding] = []

    for path in tracked_files(repo_root):
        if not is_source_file(path):
            continue
        findings.extend(check_python_module_name(path))
        text = source_text(repo_root, path)
        names = declaration_names(path, text)
        findings.extend(check_duplicate_declarations(path, names))
        findings.extend(check_meaningless_names(path, names))

    if not findings:
        print("Code quality audit passed.")
        return 0

    print("Code quality audit failed:")
    for finding in findings:
        print(f"- [{finding.rule}] {finding.path}: {finding.detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

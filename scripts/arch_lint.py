#!/usr/bin/env python3
"""Architecture Lint — Enforce dependency direction and size constraints.

Usage:
    python scripts/arch_lint.py src/              # Check dependency direction
    python scripts/arch_lint.py src/ --size-check # Also check function/class size

Exit codes:
    0 = All checks passed
    1 = Violations found
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Layer definitions: lower number = lower layer
LAYER_ORDER: dict[str, int] = {
    "types": 0,
    "config": 1,
    "repository": 2,
    "repo": 2,
    "service": 3,
    "api": 4,
    "routes": 4,
    "runtime": 5,
    "app": 5,
}

# Keywords that indicate layer membership in path
# IMPORTANT: Use exact directory/file name matching, not substring matching,
# to avoid false positives (e.g. "capital_utils" should NOT match "api").
LAYER_KEYWORDS: dict[str, int] = {
    "types": 0,
    "type": 0,
    "config": 1,
    "configs": 1,
    "repository": 2,
    "repositories": 2,
    "repo": 2,
    "repos": 2,
    "service": 3,
    "services": 3,
    "api": 4,
    "apis": 4,
    "routes": 4,
    "route": 4,
    "cli": 4,
    "runtime": 5,
    "runtimes": 5,
    "app": 5,
    "apps": 5,
}


def _match_layer_keyword(part: str) -> int | None:
    """Match a path component to a layer number using exact match only.

    This avoids substring matching bugs (e.g. "capital" containing "api").
    """
    part_lower = part.lower()
    return LAYER_KEYWORDS.get(part_lower)

MAX_FUNCTION_LINES = 30
MAX_CLASS_LINES = 200


@dataclass
class Violation:
    file: str
    line: int
    rule: str
    message: str
    severity: str = "CRITICAL"

    def __str__(self) -> str:
        return f"[{self.severity}] {self.file}:{self.line} — {self.rule}: {self.message}"


@dataclass
class LintResult:
    violations: list[Violation] = field(default_factory=list)
    files_checked: int = 0

    @property
    def passed(self) -> bool:
        critical = [v for v in self.violations if v.severity == "CRITICAL"]
        return len(critical) == 0


def detect_layer(filepath: Path, src_root: str) -> int | None:
    """Detect which layer a file belongs to based on its path.

    Uses exact directory name matching to avoid false positives.
    For example, 'capital_utils' will NOT be matched as 'api' layer.
    """
    rel = filepath.relative_to(src_root).as_posix()
    parts = rel.split("/")
    for part in parts:
        layer = _match_layer_keyword(part)
        if layer is not None:
            return layer
    return None


def detect_import_layer(import_name: str, package_root: str) -> int | None:
    """Detect which layer an import targets.

    Uses exact module name matching to avoid false positives.
    """
    parts = import_name.split(".")
    for part in parts:
        layer = _match_layer_keyword(part)
        if layer is not None:
            return layer
    return None


def check_imports(filepath: Path, src_root: str, package_name: str) -> list[Violation]:
    """Check that a file's imports respect dependency direction."""
    violations: list[Violation] = []
    source_layer = detect_layer(filepath, src_root)
    if source_layer is None:
        return violations

    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    for node in ast.walk(tree):
        import_name: str | None = None
        line = node.lineno

        if isinstance(node, ast.Import):
            for alias in node.names:
                import_name = alias.name
                import_layer = detect_import_layer(import_name, package_name)
                if import_layer is not None and import_layer > source_layer:
                    violations.append(Violation(
                        file=str(filepath),
                        line=line,
                        rule="R001",
                        message=(
                            f"Layer {source_layer} imports from Layer {import_layer} "
                            f"({import_name}). Reverse direction violation."
                        ),
                    ))

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_name = node.module
                import_layer = detect_import_layer(import_name, package_name)
                if import_layer is not None and import_layer > source_layer:
                    violations.append(Violation(
                        file=str(filepath),
                        line=line,
                        rule="R001",
                        message=(
                            f"Layer {source_layer} imports from Layer {import_layer} "
                            f"(from {import_name}). Reverse direction violation."
                        ),
                    ))

    return violations


def check_size(filepath: Path) -> list[Violation]:
    """Check function and class size limits."""
    violations: list[Violation] = []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
            if lines > MAX_FUNCTION_LINES:
                violations.append(Violation(
                    file=str(filepath),
                    line=node.lineno,
                    rule="R007",
                    message=f"Function '{node.name}' is {lines} lines (max {MAX_FUNCTION_LINES})",
                    severity="MEDIUM",
                ))

        elif isinstance(node, ast.ClassDef):
            lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
            if lines > MAX_CLASS_LINES:
                violations.append(Violation(
                    file=str(filepath),
                    line=node.lineno,
                    rule="R007",
                    message=f"Class '{node.name}' is {lines} lines (max {MAX_CLASS_LINES})",
                    severity="MEDIUM",
                ))

    return violations


def check_bare_except(filepath: Path) -> list[Violation]:
    """Check for bare except clauses."""
    violations: list[Violation] = []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                violations.append(Violation(
                    file=str(filepath),
                    line=node.lineno,
                    rule="R002",
                    message="Bare except clause. Catch a specific exception type.",
                ))
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                violations.append(Violation(
                    file=str(filepath),
                    line=node.lineno,
                    rule="R002",
                    message="Catching generic Exception. Catch a specific exception type.",
                    severity="HIGH",
                ))

    return violations


def check_print_statements(filepath: Path) -> list[Violation]:
    """Check for print() statements in source code."""
    violations: list[Violation] = []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                violations.append(Violation(
                    file=str(filepath),
                    line=node.lineno,
                    rule="R006",
                    message="print() statement found. Use structlog instead.",
                    severity="MEDIUM",
                ))

    return violations


def lint_directory(src_dir: Path, size_check: bool = False) -> LintResult:
    """Run all architecture checks on a source directory."""
    result = LintResult()
    package_name = src_dir.name

    for py_file in sorted(src_dir.rglob("*.py")):
        if py_file.name.startswith("."):
            continue
        result.files_checked += 1
        result.violations.extend(check_imports(py_file, str(src_dir), package_name))
        result.violations.extend(check_bare_except(py_file))
        result.violations.extend(check_print_statements(py_file))
        if size_check:
            result.violations.extend(check_size(py_file))

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <src_dir> [--size-check]")
        sys.exit(2)

    src_dir = Path(sys.argv[1])
    size_check = "--size-check" in sys.argv

    if not src_dir.is_dir():
        print(f"Error: '{src_dir}' is not a directory")
        sys.exit(2)

    result = lint_directory(src_dir, size_check=size_check)

    if result.violations:
        for v in sorted(result.violations, key=lambda x: (x.severity != "CRITICAL", x.file, x.line)):
            print(v)
        print(f"\n{len(result.violations)} violation(s) found in {result.files_checked} file(s)")
    else:
        print(f"OK — {result.files_checked} file(s) checked, no violations")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()

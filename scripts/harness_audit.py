#!/usr/bin/env python3
"""Harness Audit — Full project harness health report.

Checks project structure, configuration, rules compliance, and generates
a comprehensive health report.

Usage:
    python scripts/harness_audit.py [project_root]

Exit codes:
    0 = Healthy harness
    1 = Issues found (warnings or errors)
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AuditItem:
    category: str
    check: str
    status: str  # "pass" | "warn" | "fail"
    detail: str


@dataclass
class AuditReport:
    items: list[AuditItem] = field(default_factory=list)
    project_root: Path | None = None

    @property
    def pass_count(self) -> int:
        return sum(1 for i in self.items if i.status == "pass")

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.items if i.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items if i.status == "fail")

    @property
    def health_score(self) -> float:
        total = len(self.items)
        if total == 0:
            return 0.0
        return (self.pass_count + 0.5 * self.warn_count) / total * 100


def check_required_files(root: Path) -> list[AuditItem]:
    """Check for required harness files."""
    items: list[AuditItem] = []
    required = {
        "AGENTS.md": "Agent navigation document",
        "RULES.md": "Machine-enforceable rules",
        "pyproject.toml": "Project configuration",
    }
    for filename, description in required.items():
        filepath = root / filename
        if filepath.exists():
            size = filepath.stat().st_size
            items.append(AuditItem(
                category="Structure",
                check=filename,
                status="pass",
                detail=f"Exists ({size} bytes)",
            ))
        else:
            items.append(AuditItem(
                category="Structure",
                check=filename,
                status="fail",
                detail=f"Missing — {description}",
            ))
    return items


def check_directory_structure(root: Path) -> list[AuditItem]:
    """Check for expected directory layout."""
    items: list[AuditItem] = []
    expected_dirs = [
        "src",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/evals",
        "scripts",
    ]
    for dirpath in expected_dirs:
        full = root / dirpath
        if full.is_dir():
            items.append(AuditItem(
                category="Structure",
                check=dirpath + "/",
                status="pass",
                detail="Directory exists",
            ))
        else:
            items.append(AuditItem(
                category="Structure",
                check=dirpath + "/",
                status="warn",
                detail="Directory missing (recommended)",
            ))
    return items


def check_src_layers(root: Path) -> list[AuditItem]:
    """Check if src/ follows the layer structure."""
    items: list[AuditItem] = []
    src_dir = root / "src"
    if not src_dir.is_dir():
        return items

    # Find package directories
    packages = [d for d in src_dir.iterdir() if d.is_dir() and (d / "__init__.py").exists()]
    if not packages:
        items.append(AuditItem(
            category="Layers",
            check="Package structure",
            status="fail",
            detail="No Python packages found in src/",
        ))
        return items

    for pkg in packages:
        items.append(AuditItem(
            category="Layers",
            check=f"Package: {pkg.name}",
            status="pass",
            detail=f"Package found at {pkg.relative_to(root)}",
        ))

        expected_layers = ["types", "config", "repository", "service", "api", "runtime"]
        for layer in expected_layers:
            layer_path = pkg / layer
            layer_file = pkg / f"{layer}.py"
            if layer_path.is_dir() or layer_file.exists():
                items.append(AuditItem(
                    category="Layers",
                    check=f"  Layer: {layer}",
                    status="pass",
                    detail="Present",
                ))
            else:
                items.append(AuditItem(
                    category="Layers",
                    check=f"  Layer: {layer}",
                    status="warn",
                    detail="Not found (optional for some projects)",
                ))
    return items


def check_agents_md(root: Path) -> list[AuditItem]:
    """Validate AGENTS.md content quality."""
    items: list[AuditItem] = []
    agents_file = root / "AGENTS.md"
    if not agents_file.exists():
        return items

    content = agents_file.read_text(encoding="utf-8")
    sections = {
        "## Purpose": "Project purpose defined",
        "## Architecture": "Architecture overview present",
        "## Development Workflow": "Development workflow defined",
        "## Key Entry Points": "Entry points documented",
        "## Forbidden Actions": "Constraints documented",
    }

    for section, description in sections.items():
        if section.lower() in content.lower():
            items.append(AuditItem(
                category="AGENTS.md",
                check=description,
                status="pass",
                detail=f"Section '{section}' found",
            ))
        else:
            items.append(AuditItem(
                category="AGENTS.md",
                check=description,
                status="warn",
                detail=f"Section '{section}' missing",
            ))
    return items


def check_rules_md(root: Path) -> list[AuditItem]:
    """Validate RULES.md content quality."""
    items: list[AuditItem] = []
    rules_file = root / "RULES.md"
    if not rules_file.exists():
        return items

    content = rules_file.read_text(encoding="utf-8")

    # Count rules
    rule_count = content.count("## R")
    items.append(AuditItem(
        category="RULES.md",
        check="Rule count",
        status="pass" if rule_count >= 3 else "warn",
        detail=f"{rule_count} rules defined",
    ))

    # Check for enforcement info
    if "enforced by" in content.lower():
        items.append(AuditItem(
            category="RULES.md",
            check="Enforcement defined",
            status="pass",
            detail="Rules specify enforcement mechanisms",
        ))
    else:
        items.append(AuditItem(
            category="RULES.md",
            check="Enforcement defined",
            status="warn",
            detail="Rules should specify how they are enforced",
        ))

    if "severity" in content.lower():
        items.append(AuditItem(
            category="RULES.md",
            check="Severity levels",
            status="pass",
            detail="Rules specify severity levels",
        ))
    else:
        items.append(AuditItem(
            category="RULES.md",
            check="Severity levels",
            status="warn",
            detail="Rules should specify severity levels",
        ))
    return items


def check_pyproject(root: Path) -> list[AuditItem]:
    """Validate pyproject.toml has required tool configurations."""
    items: list[AuditItem] = []
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return items

    content = pyproject.read_text(encoding="utf-8")

    tools = {
        "tool.ruff": "Ruff linter configured",
        "tool.mypy": "Mypy type checker configured",
        "tool.pytest": "Pytest configured",
        "tool.coverage": "Coverage configured",
    }

    for key, description in tools.items():
        if key in content:
            items.append(AuditItem(
                category="pyproject.toml",
                check=description,
                status="pass",
                detail=f"[{key}] found",
            ))
        else:
            items.append(AuditItem(
                category="pyproject.toml",
                check=description,
                status="warn",
                detail=f"[{key}] missing",
            ))

    # Check for strict mypy
    if "strict = true" in content:
        items.append(AuditItem(
            category="pyproject.toml",
            check="Mypy strict mode",
            status="pass",
            detail="Strict type checking enabled",
        ))
    else:
        items.append(AuditItem(
            category="pyproject.toml",
            check="Mypy strict mode",
            status="warn",
            detail="Consider enabling strict = true for mypy",
        ))

    # Check coverage threshold
    if "fail_under" in content:
        items.append(AuditItem(
            category="pyproject.toml",
            check="Coverage threshold",
            status="pass",
            detail="Coverage fail threshold set",
        ))
    else:
        items.append(AuditItem(
            category="pyproject.toml",
            check="Coverage threshold",
            status="warn",
            detail="No coverage fail threshold configured",
        ))
    return items


def check_type_coverage(root: Path) -> list[AuditItem]:
    """Quick check for type annotation coverage in source files."""
    items: list[AuditItem] = []
    src_dir = root / "src"
    if not src_dir.is_dir():
        return items

    total_functions = 0
    annotated_functions = 0

    for py_file in src_dir.rglob("*.py"):
        if py_file.name.startswith("."):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):  # Only public functions
                    total_functions += 1
                    if node.returns is not None and all(
                        arg.annotation is not None
                        for arg in node.args.args
                        if arg.arg != "self" and arg.arg != "cls"
                    ):
                        annotated_functions += 1

    if total_functions > 0:
        coverage = annotated_functions / total_functions * 100
        status = "pass" if coverage >= 80 else ("warn" if coverage >= 50 else "fail")
        items.append(AuditItem(
            category="Type Safety",
            check="Public function annotations",
            status=status,
            detail=f"{annotated_functions}/{total_functions} ({coverage:.0f}%) public functions annotated",
        ))
    else:
        items.append(AuditItem(
            category="Type Safety",
            check="Public function annotations",
            status="pass",
            detail="No public functions to check",
        ))

    return items


def run_audit(root: Path) -> AuditReport:
    """Run all audit checks and return a report."""
    report = AuditReport(project_root=root)
    report.items.extend(check_required_files(root))
    report.items.extend(check_directory_structure(root))
    report.items.extend(check_src_layers(root))
    report.items.extend(check_agents_md(root))
    report.items.extend(check_rules_md(root))
    report.items.extend(check_pyproject(root))
    report.items.extend(check_type_coverage(root))
    return report


def print_report(report: AuditReport) -> None:
    """Print a formatted audit report."""
    print("=" * 60)
    print("  Python Harness Engineering — Audit Report")
    print(f"  Project: {report.project_root}")
    print("=" * 60)

    current_category = ""
    for item in report.items:
        if item.category != current_category:
            current_category = item.category
            print(f"\n  [{current_category}]")

        icon = {"pass": "+", "warn": "!", "fail": "X"}[item.status]
        print(f"    {icon}  {item.check}: {item.detail}")

    print("\n" + "=" * 60)
    print(f"  Results: {report.pass_count} passed, {report.warn_count} warnings, {report.fail_count} failures")
    print(f"  Health Score: {report.health_score:.0f}/100")

    if report.health_score >= 90:
        print("  Status: HEALTHY")
    elif report.health_score >= 70:
        print("  Status: NEEDS IMPROVEMENT")
    else:
        print("  Status: CRITICAL — significant harness gaps found")
    print("=" * 60)


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not root.is_dir():
        print(f"Error: '{root}' is not a directory")
        sys.exit(2)

    report = run_audit(root)
    print_report(report)

    sys.exit(1 if report.fail_count > 0 else 0)


if __name__ == "__main__":
    main()

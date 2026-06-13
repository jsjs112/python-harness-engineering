#!/usr/bin/env python3
"""Harness Init — Scaffold a new harness-engineered Python project.

Creates the full project structure with templates, scripts, and
configuration files in one command.

Usage:
    python scripts/harness_init.py <project_name> [--output-dir <dir>]

Example:
    python scripts/harness_init.py order_system
    python scripts/harness_init.py my_project --output-dir /tmp/projects

Exit codes:
    0 = Success
    1 = Error (directory exists, invalid name, etc.)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# Layer directories for the six-layer architecture
LAYER_DIRS: list[str] = ["repository", "service", "api", "runtime"]

# Source files to create in the package root
PACKAGE_FILES: list[str] = [
    "__init__.py",
    "types.py",
    "config.py",
]

# Test subdirectories
TEST_DIRS: list[str] = ["unit", "integration", "evals"]

# Script files to copy from this skill
SKILL_SCRIPTS: list[str] = ["arch_lint.py", "stability_gate.py", "harness_audit.py", "harness_init.py"]

# Template mapping: (template_name, destination_name)
TEMPLATE_MAP: list[tuple[str, str]] = [
    ("AGENTS.md", "AGENTS.md"),
    ("RULES.md", "RULES.md"),
    ("pyproject.toml", "pyproject.toml"),
    ("conftest_root.py", "tests/conftest.py"),
    ("conftest_unit.py", "tests/unit/conftest.py"),
    ("conftest_integration.py", "tests/integration/conftest.py"),
    ("conftest_evals.py", "tests/evals/conftest.py"),
]

# Minimal starter content for key files
TYPES_PY_CONTENT = '''"""Layer 0: Pure data types.

Zero imports from project code. Third-party type-only imports allowed.
Define dataclasses, enums, Protocol interfaces here.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


# Example:
# class OrderStatus(str, Enum):
#     CREATED = "created"
#     CONFIRMED = "confirmed"
#
# @dataclass(frozen=True)
# class Order:
#     id: str
#     user_id: str
#     status: OrderStatus = OrderStatus.CREATED
#
# class OrderRepository(Protocol):
#     def save(self, order: Order) -> None: ...
#     def find_by_id(self, order_id: str) -> Order | None: ...
'''

CONFIG_PY_CONTENT = '''"""Layer 1: Configuration.

Imports only from Layer 0 (types). Manages all environment-dependent settings.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    log_level: str = "INFO"

    # Add your config fields here:
    # database_host: str = "localhost"
    # database_port: int = 5432


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    # Implementation uses os.environ or .env file
    return AppConfig()
'''

INIT_PY_CONTENT = '''"""Package root. Export public API symbols here."""
'''

TEST_INIT_CONTENT = ""  # Empty __init__.py for test dirs

SAMPLE_UNIT_TEST = '''"""Sample unit test. Replace with real tests."""

import pytest


class TestSample:
    """Replace with your actual unit tests."""

    def test_placeholder(self) -> None:
        """This test exists so pytest has something to collect.
        Delete this file once you add real tests."""
        assert True
'''

SAMPLE_EVAL_TEST = '''"""Sample eval test. Replace with real capability tests."""

import pytest


@pytest.mark.eval
class TestSampleCapability:
    """Replace with your actual eval tests.

    Eval tests verify agent-facing capabilities BEFORE implementation.
    They run as part of the stability gate before every merge.
    """

    def test_placeholder(self) -> None:
        """This test exists so pytest has something to collect.
        Delete this file once you add real evals."""
        assert True
'''


def validate_project_name(name: str) -> bool:
    """Validate that the project name is a valid Python package name."""
    if not name.isidentifier():
        return False
    if name.startswith("_"):
        return False
    return True


def find_skill_dir() -> Path:
    """Find the skill directory containing templates and scripts."""
    # harness_init.py is in scripts/, so skill root is parent
    return Path(__file__).resolve().parent.parent


def scaffold_project(
    project_name: str,
    output_dir: Path,
    skill_dir: Path,
) -> Path:
    """Create the full project structure."""
    project_root = output_dir / project_name
    templates_dir = skill_dir / "templates"
    scripts_dir = skill_dir / "scripts"

    # 1. Create project root
    project_root.mkdir(parents=True)

    # 2. Copy templates
    for template_name, dest_path in TEMPLATE_MAP:
        src = templates_dir / template_name
        dst = project_root / dest_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
            # Replace placeholder package name in conftest files
            if template_name.startswith("conftest_"):
                content = dst.read_text(encoding="utf-8")
                content = content.replace("your_package_name", project_name)
                dst.write_text(content, encoding="utf-8")
        else:
            print(f"  Warning: template '{template_name}' not found, skipping")

    # 3. Copy pyproject.toml and replace placeholder
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        content = content.replace("your-project-name", project_name.replace("_", "-"))
        content = content.replace("your_package_name", project_name)
        pyproject.write_text(content, encoding="utf-8")

    # 4. Create source directory structure
    pkg_dir = project_root / "src" / project_name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    for layer_dir in LAYER_DIRS:
        layer_path = pkg_dir / layer_dir
        layer_path.mkdir(exist_ok=True)
        (layer_path / "__init__.py").write_text("", encoding="utf-8")

    # 5. Create package files
    (pkg_dir / "__init__.py").write_text(INIT_PY_CONTENT, encoding="utf-8")
    (pkg_dir / "types.py").write_text(TYPES_PY_CONTENT, encoding="utf-8")
    (pkg_dir / "config.py").write_text(CONFIG_PY_CONTENT, encoding="utf-8")

    # 6. Create test __init__.py files (root + each tier)
    (project_root / "tests" / "__init__.py").write_text(TEST_INIT_CONTENT, encoding="utf-8")
    for test_dir in TEST_DIRS:
        test_path = project_root / "tests" / test_dir
        test_path.mkdir(parents=True, exist_ok=True)
        (test_path / "__init__.py").write_text(TEST_INIT_CONTENT, encoding="utf-8")

    # 7. Create sample test files
    (project_root / "tests" / "unit" / "test_sample.py").write_text(
        SAMPLE_UNIT_TEST, encoding="utf-8"
    )
    (project_root / "tests" / "evals" / "test_sample_capability.py").write_text(
        SAMPLE_EVAL_TEST, encoding="utf-8"
    )

    # 8. Create additional directories
    (project_root / "scripts").mkdir(exist_ok=True)
    (project_root / "docs").mkdir(exist_ok=True)

    # 9. Copy skill scripts
    for script_name in SKILL_SCRIPTS:
        src = scripts_dir / script_name
        dst = project_root / "scripts" / script_name
        if src.exists():
            shutil.copy2(src, dst)

    return project_root


def print_summary(project_root: Path, project_name: str) -> None:
    """Print a summary of what was created."""
    print()
    print("=" * 55)
    print(f"  Harness-Engineered Project: {project_name}")
    print(f"  Location: {project_root}")
    print("=" * 55)
    print()
    print("  Created structure:")
    print(f"    {project_root}/")
    print(f"    +-- AGENTS.md          (agent navigation)")
    print(f"    +-- RULES.md           (enforceable constraints)")
    print(f"    +-- pyproject.toml     (tool configuration)")
    print(f"    +-- src/{project_name}/")
    print(f"    |   +-- types.py       (Layer 0: data types)")
    print(f"    |   +-- config.py      (Layer 1: configuration)")
    print(f"    |   +-- repository/    (Layer 2: data access)")
    print(f"    |   +-- service/       (Layer 3: business logic)")
    print(f"    |   +-- api/           (Layer 4: interface)")
    print(f"    |   +-- runtime/       (Layer 5: DI + bootstrap)")
    print(f"    +-- tests/")
    print(f"    |   +-- conftest.py    (shared fixtures)")
    print(f"    |   +-- unit/          (isolated tests)")
    print(f"    |   +-- integration/   (component tests)")
    print(f"    |   +-- evals/         (capability tests)")
    print(f"    +-- scripts/")
    print(f"    |   +-- arch_lint.py")
    print(f"    |   +-- stability_gate.py")
    print(f"    |   +-- harness_audit.py")
    print(f"    +-- docs/")
    print()
    print("  Next steps:")
    print(f"    cd {project_root}")
    print(f'    pip install -e ".[dev]"')
    print(f"    python scripts/stability_gate.py --dry-run")
    print(f"    python scripts/harness_audit.py")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a harness-engineered Python project."
    )
    parser.add_argument(
        "project_name",
        help="Project name (must be a valid Python identifier)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to create the project in (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without making changes",
    )
    args = parser.parse_args()

    # Validate
    if not validate_project_name(args.project_name):
        print(f"Error: '{args.project_name}' is not a valid Python package name.")
        print("Use lowercase with underscores (e.g., order_system, my_project).")
        sys.exit(1)

    project_root = args.output_dir / args.project_name
    if project_root.exists():
        print(f"Error: '{project_root}' already exists.")
        print("Choose a different name or delete the existing directory.")
        sys.exit(1)

    skill_dir = find_skill_dir()

    # Dry run: preview what would be created
    if args.dry_run:
        print(f"[DRY RUN] Would create project: {args.project_name}")
        print(f"[DRY RUN] Location: {project_root}")
        print()
        print("[DRY RUN] Structure:")
        print(f"  {project_root}/")
        print(f"  +-- AGENTS.md, RULES.md, pyproject.toml")
        print(f"  +-- src/{args.project_name}/")
        print(f"  |   +-- __init__.py, types.py, config.py")
        for d in LAYER_DIRS:
            print(f"  |   +-- {d}/__init__.py")
        print(f"  +-- tests/conftest.py (shared fixtures)")
        for d in TEST_DIRS:
            print(f"  +-- tests/{d}/conftest.py + __init__.py")
        print(f"  +-- scripts/ ({', '.join(SKILL_SCRIPTS)})")
        print(f"  +-- docs/")
        print()
        print("[DRY RUN] No files were created. Run without --dry-run to scaffold.")
        return

    print(f"Scaffolding harness-engineered project: {args.project_name}")
    print(f"Output: {args.output_dir}")
    print()

    try:
        root = scaffold_project(args.project_name, args.output_dir, skill_dir)
        print_summary(root, args.project_name)
    except Exception as e:
        print(f"Error during scaffolding: {e}")
        # Cleanup partial creation
        if project_root.exists():
            shutil.rmtree(project_root)
        sys.exit(1)


if __name__ == "__main__":
    main()

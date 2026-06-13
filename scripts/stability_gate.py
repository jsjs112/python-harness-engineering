#!/usr/bin/env python3
"""Stability Gate — Pre-merge quality validation.

Runs all quality checks in sequence with fail-fast behavior.
All gates must pass for the change to be mergeable.

Usage:
    python scripts/stability_gate.py            # Full gate
    python scripts/stability_gate.py --dry-run  # Preview what will be checked

Gates (in order):
    1. Architecture lint (arch_lint.py)
    2. Ruff check (lint + style)
    3. Mypy (type safety)
    4. Pytest unit tests
    5. Pytest integration tests
    6. Pytest evals + coverage

Exit codes:
    0 = All gates passed
    1 = One or more gates failed
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Gate:
    name: str
    command: list[str]
    description: str
    critical: bool = True


GATES: list[Gate] = [
    Gate(
        name="Architecture Lint",
        command=[sys.executable, "scripts/arch_lint.py", "src/", "--size-check"],
        description="Check dependency direction and size constraints",
    ),
    Gate(
        name="Ruff Check",
        command=[sys.executable, "-m", "ruff", "check", "src/"],
        description="Lint and style validation",
    ),
    Gate(
        name="Mypy",
        command=[sys.executable, "-m", "mypy", "src/"],
        description="Static type checking",
    ),
    Gate(
        name="Unit Tests",
        command=[sys.executable, "-m", "pytest", "tests/unit", "-v", "--tb=short"],
        description="Unit test suite",
    ),
    Gate(
        name="Integration Tests",
        command=[
            sys.executable, "-m", "pytest", "tests/integration",
            "-v", "--tb=short", "--no-header",
        ],
        description="Integration test suite",
        critical=False,  # Allow skip if no integration tests exist
    ),
    Gate(
        name="Evals + Coverage",
        command=[
            sys.executable, "-m", "pytest", "tests/evals",
            "--cov=src", "--cov-report=term-missing", "--cov-fail-under=80",
            "-v", "--tb=short",
        ],
        description="Evaluation tests with coverage threshold",
    ),
]


@dataclass(frozen=True)
class GateResult:
    gate: Gate
    passed: bool
    duration: float
    output: str
    skipped: bool = False


def run_gate(gate: Gate, project_root: Path) -> GateResult:
    """Execute a single gate and return the result."""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            gate.command,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=300,
        )
        duration = time.monotonic() - start
        passed = proc.returncode == 0
        output = proc.stdout + proc.stderr

        # Handle "no tests collected" as skip, not failure
        if not passed and "no tests ran" in output.lower():
            return GateResult(gate=gate, passed=True, duration=duration, output=output, skipped=True)

        return GateResult(gate=gate, passed=passed, duration=duration, output=output)

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return GateResult(gate=gate, passed=False, duration=duration, output="TIMEOUT: exceeded 300s")
    except FileNotFoundError as e:
        duration = time.monotonic() - start
        return GateResult(gate=gate, passed=False, duration=duration, output=str(e))


def print_result(result: GateResult) -> None:
    """Print a formatted gate result."""
    if result.skipped:
        status = "SKIP"
        color = "\033[33m"  # yellow
    elif result.passed:
        status = "PASS"
        color = "\033[32m"  # green
    else:
        status = "FAIL"
        color = "\033[31m"  # red

    reset = "\033[0m"
    print(f"  {color}{status}{reset}  {result.gate.name} ({result.duration:.1f}s)")

    if not result.passed and not result.skipped:
        # Print last few lines of output for context
        lines = result.output.strip().split("\n")
        for line in lines[-5:]:
            print(f"         {line}")
        print()


def dry_run() -> None:
    """Print what gates will be checked without running them."""
    print("Stability Gate — Dry Run")
    print("=" * 50)
    for i, gate in enumerate(GATES, 1):
        crit = "CRITICAL" if gate.critical else "OPTIONAL"
        print(f"  {i}. [{crit}] {gate.name}")
        print(f"     {gate.description}")
        print(f"     Command: {' '.join(gate.command)}")
        print()


def main() -> None:
    project_root = Path.cwd()

    if "--dry-run" in sys.argv:
        dry_run()
        return

    print("Stability Gate — Running all checks")
    print("=" * 50)

    results: list[GateResult] = []
    failed = False

    for gate in GATES:
        result = run_gate(gate, project_root)
        results.append(result)
        print_result(result)

        if not result.passed and not result.skipped:
            if gate.critical:
                failed = True
                break  # Fail-fast: stop on first critical failure
            print(f"  (Non-critical gate failed, continuing...)")

    # Summary
    print("=" * 50)
    passed_count = sum(1 for r in results if r.passed)
    total = len(results)
    total_time = sum(r.duration for r in results)

    if failed:
        print(f"BLOCKED — {passed_count}/{total} gates passed ({total_time:.1f}s)")
        print("Fix the failing gate before merging.")
    else:
        print(f"CLEAR — {passed_count}/{total} gates passed ({total_time:.1f}s)")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

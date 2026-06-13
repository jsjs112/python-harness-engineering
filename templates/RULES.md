# Rules — [PROJECT_NAME]

> These rules are machine-enforceable. Violations MUST block merges.
> Run `python scripts/stability_gate.py` to validate all rules at once.

## R001: Dependency Direction

Layers must only import from lower-numbered layers (types → config → repository → service → api → runtime).

- **Severity**: CRITICAL
- **Enforced by**: `python scripts/arch_lint.py`
- **Rationale**: Reverse imports create circular dependencies and make the codebase fragile

## R002: No Bare Excepts

All exception handling must catch specific exception types. Bare `except:` and `except Exception:` are forbidden.

- **Severity**: CRITICAL
- **Enforced by**: ruff rule E722 + custom check in arch_lint.py
- **Rationale**: Bare excepts silently swallow bugs and make debugging impossible

## R003: Type Annotations Required

All public function signatures (non-underscore-prefixed) must have complete type annotations, including return types.

- **Severity**: HIGH
- **Enforced by**: `mypy --strict src/`
- **Rationale**: Type annotations are the primary interface contract for both humans and agents

## R004: Test Coverage Threshold

Every change must include tests. Line coverage must not fall below 80%. Critical paths (payment, auth, data mutation) require 100% branch coverage.

- **Severity**: CRITICAL
- **Enforced by**: `pytest --cov=src --cov-fail-under=80`
- **Rationale**: Untested code is unverified code; coverage regression indicates missing validation

## R005: No Mutable Defaults

Function parameters must not use mutable default values (list, dict, set). Use `None` with factory initialization.

- **Severity**: HIGH
- **Enforced by**: ruff rule B006
- **Rationale**: Mutable defaults create shared state between function calls

## R006: Structured Logging Only

Use `structlog` for all logging. No `print()` statements in `src/`. No `logging` stdlib usage.

- **Severity**: MEDIUM
- **Enforced by**: ruff custom rule + grep in arch_lint.py
- **Rationale**: Structured logs enable automated monitoring and debugging

## R007: Function Size Limit

Functions must not exceed 30 lines (excluding docstrings and comments). Classes must not exceed 200 lines.

- **Severity**: MEDIUM
- **Enforced by**: `python scripts/arch_lint.py --size-check`
- **Rationale**: Small functions are easier to test, understand, and modify

## R008: No Wildcard Imports

`from module import *` is forbidden in all project code.

- **Severity**: HIGH
- **Enforced by**: ruff rule F403
- **Rationale**: Wildcard imports make it impossible to trace symbol origins

## R009: Exception Chaining

When catching and re-raising exceptions, always use `raise NewError(...) from original_error`.

- **Severity**: MEDIUM
- **Enforced by**: ruff rule B904
- **Rationale**: Preserves the original traceback for debugging

## R010: Frozen Data Types

All data transfer objects (DTOs) and value objects must use `@dataclass(frozen=True)` or equivalent immutable patterns.

- **Severity**: MEDIUM
- **Enforced by**: arch_lint.py custom check
- **Rationale**: Immutable data prevents unexpected mutations across layers

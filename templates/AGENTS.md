# Project: [PROJECT_NAME]

## Purpose

[One sentence describing what this project does and its core value proposition.]

## Architecture

This project follows a six-layer harness architecture:
- **Layer 0 (types/)**: Pure data types, enums, Protocol interfaces — zero project imports
- **Layer 1 (config/)**: Environment-dependent settings — imports only from types
- **Layer 2 (repository/)**: Data access and external API clients — imports from types + config
- **Layer 3 (service/)**: Business logic and domain rules — imports from types + config + repository
- **Layer 4 (api/)**: HTTP/gRPC handlers, CLI — imports from all below
- **Layer 5 (runtime/)**: DI, bootstrap, lifecycle — imports from all

Dependency direction: lower layers NEVER import from higher layers.

## Development Workflow

1. **Read RULES.md** before making any changes
2. **Write tests first** — define expected behavior before implementation
3. **Implement with constraints** — follow dependency direction, add type annotations, use structlog
4. **Run the stability gate** before committing:
   ```bash
   python scripts/stability_gate.py
   ```
5. **All checks must pass** — architecture lint, ruff, mypy, pytest

## Key Entry Points

- **Main application**: `src/[package]/runtime/app.py`
- **API routes**: `src/[package]/api/`
- **Business logic**: `src/[package]/service/`
- **Data access**: `src/[package]/repository/`
- **Configuration**: `src/[package]/config.py`
- **Type definitions**: `src/[package]/types.py`

## Tech Stack

- **Language**: Python 3.11+
- **Linting**: ruff (style + safety rules)
- **Type checking**: mypy --strict
- **Testing**: pytest (unit + integration + evals)
- **Logging**: structlog (structured, context-aware)
- **Web framework**: [FastAPI / Flask / etc.]
- **Database**: [PostgreSQL / SQLite / etc.] via [SQLAlchemy / etc.]

## Forbidden Actions

- Never import from a higher-numbered layer into a lower-numbered layer
- Never use bare `except:` or `except Exception:`
- Never use `print()` for output — use `structlog`
- Never use mutable default arguments
- Never use `from module import *`
- Never modify `types.py` without verifying all dependent layers still pass
- Never skip the stability gate — if it fails, fix before merging
- Never add a dependency that violates the approved dependency list in pyproject.toml

## Testing Strategy

| Tier | Path | Purpose | When |
|------|------|---------|------|
| Unit | `tests/unit/` | Isolated logic verification | Every change |
| Integration | `tests/integration/` | Component interaction | Every change |
| Eval | `tests/evals/` | Agent-facing capability | Pre-merge |

Coverage minimum: 80% line coverage. Critical paths: 100% branch coverage.

## How to Run

```bash
# Install
pip install -e ".[dev]"

# Run stability gate (all checks)
python scripts/stability_gate.py

# Run individual checks
python scripts/arch_lint.py src/
ruff check src/
mypy src/
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

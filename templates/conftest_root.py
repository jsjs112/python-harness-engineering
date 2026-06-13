"""Root conftest.py — Shared fixtures for all test tiers.

Copy to: tests/conftest.py
Replace 'your_package_name' with your actual package name.

This file provides:
- app_config: Frozen AppConfig for testing
- structured_logging: Auto-resets structlog context between tests
- tmp_data_dir: Isolated temporary directory per test
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest
import structlog

# -- Import your actual config/types here --
# from your_package_name.config import AppConfig, DatabaseConfig
# from your_package_name.types import OrderRepository


# ============================================================
# Session-scoped: expensive setup, created once per test session
# ============================================================


@pytest.fixture(scope="session")
def app_config() -> "AppConfig":
    """Frozen application config for testing.

    Override DatabaseConfig to use in-memory or test database.
    """
    # Replace with your actual config construction:
    # from your_package_name.config import AppConfig, DatabaseConfig
    # return AppConfig(
    #     database=DatabaseConfig(host="localhost", name="test_db"),
    #     log_level="DEBUG",
    # )
    raise NotImplementedError(
        "Replace this fixture with your actual AppConfig construction. "
        "See templates/conftest.py for the pattern."
    )


# ============================================================
# Function-scoped: fresh state per test
# ============================================================


@pytest.fixture(autouse=True)
def structured_logging() -> Generator[None, None, None]:
    """Reset structlog context vars between tests.

    Prevents log context leaking across test boundaries.
    """
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Isolated temporary directory for test data files."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir

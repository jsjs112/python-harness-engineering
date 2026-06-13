"""Eval test conftest.py — Fixtures for agent-facing capability verification.

Copy to: tests/evals/conftest.py
Replace 'your_package_name' with your actual package name.

Eval tests verify that the system meets its high-level capability
requirements. They test the system as a black box through its public
API, simulating how an agent (or end user) would interact with it.

Eval tests MUST:
- Run before every merge (part of stability_gate.py)
- Test capability, not implementation details
- Treat failures as CRITICAL blocks (never skip or xfail)
"""

from __future__ import annotations

from typing import Generator

import pytest

# -- Import your actual types/config/service here --
# from your_package_name.config import AppConfig
# from your_package_name.service.order_service import OrderService
# from your_package_name.repository.order_repo import PostgresOrderRepository


# ============================================================
# Eval-grade service fixture
# ============================================================


@pytest.fixture(scope="module")
def eval_config() -> "AppConfig":
    """Configuration for eval environment.

    Evals may need a richer config than unit tests (e.g., real
    feature flags, production-like limits).
    """
    # from your_package_name.config import AppConfig, DatabaseConfig
    # return AppConfig(
    #     database=DatabaseConfig(
    #         host="localhost",
    #         name="eval_db",
    #         pool_size=5,  # production-like
    #     ),
    #     max_order_items=100,  # production limit
    # )
    raise NotImplementedError(
        "Replace with production-like eval configuration."
    )


@pytest.fixture(scope="module")
def eval_order_service(eval_config: "AppConfig") -> Generator["OrderService", None, None]:
    """OrderService for eval tests, scoped per module.

    Uses real (or high-fidelity fake) dependencies to verify
    end-to-end capability. Scoped to module for performance —
    evals in the same module share the service instance.

    If your evals need isolation, change scope to 'function'.
    """
    # from your_package_name.repository.order_repo import InMemoryOrderRepository
    # from your_package_name.service.order_service import OrderService
    #
    # repo = InMemoryOrderRepository()  # or real DB for full eval
    # service = OrderService(repo=repo, config=eval_config)
    # yield service
    raise NotImplementedError(
        "Replace with your actual service construction for evals. "
        "Use real or high-fidelity dependencies."
    )


# ============================================================
# Eval helper fixtures
# ============================================================


@pytest.fixture
def test_user_id() -> str:
    """Standard test user ID for eval scenarios."""
    return "eval-user-001"


@pytest.fixture
def sample_items() -> list[tuple[str, int, float]]:
    """Standard item list for eval scenarios.

    Returns a list of (sku, quantity, unit_price) tuples.
    """
    return [
        ("SKU-EVAL-001", 2, 29.99),
        ("SKU-EVAL-002", 1, 49.99),
    ]


@pytest.fixture
def idempotency_key() -> str:
    """Fresh idempotency key per test."""
    import uuid
    return str(uuid.uuid4())

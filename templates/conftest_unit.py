"""Unit test conftest.py — Fixtures with mocked dependencies.

Copy to: tests/unit/conftest.py
Replace 'your_package_name' with your actual package name.

Unit tests verify isolated logic. All external dependencies
(databases, APIs, file systems) MUST be replaced with fakes/mocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator

import pytest

# -- Import your actual types here --
# from your_package_name.types import Order, OrderItem, OrderStatus, OrderRepository


# ============================================================
# Fake implementations (in-memory, no I/O)
# ============================================================


@dataclass
class FakeOrderRepository:
    """In-memory fake of OrderRepository for unit testing.

    Mirrors the Protocol interface defined in types.py (Layer 0).
    Every test gets a fresh instance via the fixture below.
    """

    _store: dict[str, "Order"] = field(default_factory=dict)

    def save(self, order: "Order") -> None:
        self._store[order.id] = order

    def find_by_id(self, order_id: str) -> "Order | None":
        return self._store.get(order_id)

    def find_by_user(self, user_id: str) -> list["Order"]:
        return [o for o in self._store.values() if o.user_id == user_id]


# ============================================================
# Unit test fixtures
# ============================================================


@pytest.fixture
def fake_order_repo() -> FakeOrderRepository:
    """Fresh in-memory repository per test.

    Usage in tests:
        def test_something(fake_order_repo):
            fake_order_repo.save(some_order)
            result = fake_order_repo.find_by_id(some_order.id)
            assert result == some_order
    """
    return FakeOrderRepository()


@pytest.fixture
def order_service(fake_order_repo: FakeOrderRepository, app_config: "AppConfig") -> "OrderService":
    """Fully wired OrderService with fake dependencies.

    This is the primary fixture for unit testing service-layer logic.
    All dependencies are fakes — no real I/O happens.

    Usage in tests:
        def test_creates_order(order_service):
            order = order_service.create(user_id="u1", items=[("SKU", 1, 9.99)])
            assert order.status == "created"
    """
    # Replace with your actual service construction:
    # from your_package_name.service.order_service import OrderService
    # return OrderService(repo=fake_order_repo, config=app_config)
    raise NotImplementedError(
        "Replace this fixture with your actual service construction. "
        "Pattern: Service(repo=fake_repo, config=app_config)"
    )


# ============================================================
# Builder helpers (optional, for complex test data)
# ============================================================


def build_order(
    order_id: str = "test-001",
    user_id: str = "user-001",
    items: list[tuple[str, int, float]] | None = None,
    status: str = "created",
) -> "Order":
    """Builder for test Order objects. Reduces boilerplate in tests.

    Usage:
        order = build_order(items=[("SKU001", 2, 19.99)])
    """
    # Replace with your actual Order construction:
    # from your_package_name.types import Order, OrderItem, OrderStatus
    # order_items = tuple(
    #     OrderItem(sku=sku, quantity=qty, unit_price=price)
    #     for sku, qty, price in (items or [("SKU-DEFAULT", 1, 9.99)])
    # )
    # return Order(
    #     id=order_id,
    #     user_id=user_id,
    #     items=order_items,
    #     status=OrderStatus(status),
    # )
    raise NotImplementedError("Replace with your actual Order construction.")

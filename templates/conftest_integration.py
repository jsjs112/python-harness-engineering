"""Integration test conftest.py — Fixtures with real (or containerized) dependencies.

Copy to: tests/integration/conftest.py
Replace 'your_package_name' with your actual package name.

Integration tests verify component interaction. They use real
databases, caches, or external APIs (often via Docker/testcontainers).

Mark slow tests with @pytest.mark.integration so they can be
skipped in fast CI runs: pytest -m "not integration"
"""

from __future__ import annotations

from typing import Generator

import pytest

# -- Import your actual types/config here --
# from your_package_name.config import AppConfig, DatabaseConfig
# from your_package_name.repository.order_repo import PostgresOrderRepository


# ============================================================
# Database lifecycle (session-scoped)
# ============================================================


@pytest.fixture(scope="session")
def db_engine(app_config: "AppConfig") -> Generator:
    """Create a real database engine for integration tests.

    Uses the test database configured in app_config.
    Engine is created once per session and torn down after all tests.

    Prerequisites:
    - A test database must be running (local PostgreSQL, Docker, etc.)
    - Database URL is configured via app_config.database
    """
    # Replace with your actual database setup:
    # from sqlalchemy import create_engine
    # engine = create_engine(
    #     f"postgresql://{app_config.database.host}:{app_config.database.port}"
    #     f"/{app_config.database.name}",
    #     pool_size=2,
    # )
    # # Run migrations or create tables
    # Base.metadata.create_all(engine)
    # yield engine
    # # Cleanup: drop tables after all tests
    # Base.metadata.drop_all(engine)
    # engine.dispose()
    raise NotImplementedError(
        "Replace with your actual database engine setup. "
        "Pattern: create_engine() -> yield -> dispose()"
    )


@pytest.fixture(scope="session")
def db_session_factory(db_engine) -> Generator:
    """Session factory bound to the test database engine.

    Each test gets its own session via the `db_session` fixture below.
    """
    # from sqlalchemy.orm import sessionmaker
    # SessionFactory = sessionmaker(bind=db_engine)
    # yield SessionFactory
    raise NotImplementedError("Replace with your actual session factory.")


# ============================================================
# Per-test isolation
# ============================================================


@pytest.fixture
def db_session(db_session_factory) -> Generator:
    """Fresh database session per test with automatic rollback.

    Wraps each test in a transaction that is rolled back after the test,
    ensuring test isolation without the cost of recreating the database.
    """
    # connection = db_session_factory().connection()
    # transaction = connection.begin()
    # session = db_session_factory(bind=connection)
    # yield session
    # session.close()
    # transaction.rollback()
    # connection.close()
    raise NotImplementedError(
        "Replace with transaction-wrapped session for test isolation."
    )


@pytest.fixture
def order_repo(db_session) -> "PostgresOrderRepository":
    """Real repository backed by the test database session."""
    # from your_package_name.repository.order_repo import PostgresOrderRepository
    # return PostgresOrderRepository(session_factory=lambda: db_session)
    raise NotImplementedError("Replace with your actual repository construction.")


@pytest.fixture
def order_service_integration(
    order_repo, app_config: "AppConfig"
) -> "OrderService":
    """OrderService wired to real repository (not fake).

    Use this fixture to test service + repository interaction.
    """
    # from your_package_name.service.order_service import OrderService
    # return OrderService(repo=order_repo, config=app_config)
    raise NotImplementedError(
        "Replace: Service(repo=real_repo, config=app_config)"
    )

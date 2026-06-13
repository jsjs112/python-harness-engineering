# Python Harness Engineering Reference Architecture

## The Six-Layer Model

```
┌─────────────────────────────────────────────────┐
│  Layer 5: Runtime                               │
│  DI container, app bootstrap, lifecycle mgmt    │
├─────────────────────────────────────────────────┤
│  Layer 4: API                                   │
│  HTTP/gRPC handlers, CLI commands, input parse  │
├─────────────────────────────────────────────────┤
│  Layer 3: Service                               │
│  Business logic, orchestration, domain rules    │
├─────────────────────────────────────────────────┤
│  Layer 2: Repository                           │
│  Data access, ORM, external API clients         │
├─────────────────────────────────────────────────┤
│  Layer 1: Config                                │
│  Settings, env vars, feature flags              │
├─────────────────────────────────────────────────┤
│  Layer 0: Types                                 │
│  Data classes, enums, protocols, type aliases   │
└─────────────────────────────────────────────────┘
```

### Dependency Direction

A layer may ONLY import from layers with a lower number. This is the single most important rule.

```
PASS: service/imports from repository, config, types
FAIL: repository/imports from service (reverse direction)
FAIL: types/imports from config (Layer 0 must be import-free)
```

## Layer 0: Types

Pure data definitions. Zero imports from project code. Third-party type-only imports allowed (e.g., `pydantic`, `dataclasses`).

```python
# src/order_system/types.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class OrderStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderItem:
    sku: str
    quantity: int
    unit_price: float

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


@dataclass(frozen=True)
class Order:
    id: str
    user_id: str
    items: tuple[OrderItem, ...]
    status: OrderStatus = OrderStatus.CREATED

    @property
    def total(self) -> float:
        return sum(item.total for item in self.items)


class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def find_by_id(self, order_id: str) -> Order | None: ...
    def find_by_user(self, user_id: str) -> list[Order]: ...
```

Key rules for Layer 0:
- Use `frozen=True` dataclasses for immutability
- Use `tuple` instead of `list` in frozen dataclasses
- Define `Protocol` interfaces here (not implementations)
- No I/O, no side effects, no business logic beyond pure computations

## Layer 1: Config

Imports only from Layer 0. Manages all environment-dependent settings.

```python
# src/order_system/config.py
from dataclasses import dataclass, field
from pathlib import Path

from order_system.types import OrderStatus


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "orders"
    pool_size: int = 10


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    log_level: str = "INFO"
    max_order_items: int = 100
    allowed_currencies: frozenset[str] = frozenset({"USD", "EUR", "CNY"})


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    # Implementation uses os.environ or .env file
    ...
```

## Layer 2: Repository

Imports from Layer 0 (Types) and Layer 1 (Config). Implements the Protocol interfaces defined in Types.

```python
# src/order_system/repository/order_repo.py
import structlog
from sqlalchemy import select

from order_system.types import Order, OrderItem, OrderStatus, OrderRepository

logger = structlog.get_logger(__name__)


class PostgresOrderRepository:
    """Implements OrderRepository protocol using PostgreSQL."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def save(self, order: Order) -> None:
        logger.info("saving_order", order_id=order.id, status=order.status)
        with self._session_factory() as session:
            # ORM mapping logic
            session.merge(self._to_model(order))
            session.commit()

    def find_by_id(self, order_id: str) -> Order | None:
        with self._session_factory() as session:
            model = session.get(OrderModel, order_id)
            return self._to_domain(model) if model else None

    def find_by_user(self, user_id: str) -> list[Order]:
        with self._session_factory() as session:
            stmt = select(OrderModel).where(OrderModel.user_id == user_id)
            models = session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]

    def _to_model(self, order: Order) -> "OrderModel": ...
    def _to_domain(self, model: "OrderModel") -> Order: ...
```

## Layer 3: Service

Imports from Layers 0, 1, 2. Contains all business logic. This is where domain rules are enforced.

```python
# src/order_system/service/order_service.py
import structlog

from order_system.types import (
    Order, OrderItem, OrderStatus, OrderRepository,
)
from order_system.config import AppConfig
from order_system.service.errors import (
    OrderError, ValidationError, OrderNotFoundError,
)

logger = structlog.get_logger(__name__)


class OrderService:
    def __init__(self, repo: OrderRepository, config: AppConfig) -> None:
        self._repo = repo
        self._config = config

    def create(self, user_id: str, items: list[tuple[str, int, float]],
               idempotency_key: str | None = None) -> Order:
        self._validate_items(items)
        order_items = tuple(
            OrderItem(sku=sku, quantity=qty, unit_price=price)
            for sku, qty, price in items
        )
        order = Order(
            id=idempotency_key or self._generate_id(),
            user_id=user_id,
            items=order_items,
        )
        self._repo.save(order)
        logger.info("order_created", order_id=order.id, total=order.total)
        return order

    def cancel(self, order_id: str) -> Order:
        order = self._repo.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError("Order", order_id)
        if order.status not in (OrderStatus.CREATED, OrderStatus.CONFIRMED):
            raise ValidationError("status", f"Cannot cancel order in {order.status}")
        cancelled = Order(
            id=order.id, user_id=order.user_id,
            items=order.items, status=OrderStatus.CANCELLED,
        )
        self._repo.save(cancelled)
        logger.info("order_cancelled", order_id=order_id)
        return cancelled

    def _validate_items(self, items: list[tuple[str, int, float]]) -> None:
        if not items:
            raise ValidationError("items", "Order must contain at least one item")
        if len(items) > self._config.max_order_items:
            raise ValidationError("items",
                f"Order cannot exceed {self._config.max_order_items} items")
```

## Layer 4: API

Imports from all lower layers. Translates external requests into service calls. Handles HTTP/CLI concerns.

```python
# src/order_system/api/order_routes.py
from dataclasses import asdict

import structlog
from fastapi import APIRouter, HTTPException

from order_system.types import Order
from order_system.service.order_service import OrderService
from order_system.service.errors import ValidationError, OrderNotFoundError

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/orders")


@router.post("/")
def create_order(request: CreateOrderRequest, service: OrderService) -> dict:
    try:
        order = service.create(
            user_id=request.user_id,
            items=request.items,
            idempotency_key=request.idempotency_key,
        )
        return asdict(order)
    except ValidationError as e:
        logger.warning("create_order_validation_error", field=e.field, message=e.message)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{order_id}")
def get_order(order_id: str, service: OrderService) -> dict:
    order = service._repo.find_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return asdict(order)
```

## Layer 5: Runtime

Imports from all layers. Responsible for dependency injection, application bootstrap, and lifecycle management.

```python
# src/order_system/runtime/app.py
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from order_system.config import load_config
from order_system.repository.order_repo import PostgresOrderRepository
from order_system.service.order_service import OrderService
from order_system.api.order_routes import router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    logger.info("app_starting", log_level=config.log_level)
    # Initialize database, cache, etc.
    yield
    logger.info("app_stopping")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    config = load_config()

    # Dependency injection
    repo = PostgresOrderRepository(session_factory=...)
    service = OrderService(repo=repo, config=config)

    app.state.service = service
    app.include_router(router)
    return app
```

## Error Hierarchy Pattern

Each layer defines its own error namespace, inheriting from a project-wide base:

```
ProjectError (base)
├── types.ValidationError (data validation)
├── repository.RepositoryError (data access failures)
├── service.ServiceError (business rule violations)
│   ├── service.OrderError
│   ├── service.PaymentError
│   └── service.AuthError
└── api.ApiError (request/response issues)
```

Rules:
- Errors flow UP (lower layers raise, upper layers catch and translate)
- Never catch errors from a higher layer in a lower layer
- Always use `raise ... from original_error` for exception chaining
- Log errors at the boundary where they are caught, not where they are raised

## Context Management Pattern

```python
# src/order_system/runtime/context.py
from contextlib import contextmanager
from dataclasses import dataclass
import uuid

import structlog


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    user_id: str | None
    correlation_id: str | None


@contextmanager
def request_context(user_id: str | None = None):
    ctx = RequestContext(
        request_id=str(uuid.uuid4()),
        user_id=user_id,
        correlation_id=None,
    )
    structlog.contextvars.bind_contextvars(
        request_id=ctx.request_id,
        user_id=ctx.user_id,
    )
    try:
        yield ctx
    finally:
        structlog.contextvars.clear_contextvars()
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Harness Gate
on: [pull_request]

jobs:
  stability-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - name: Architecture Lint
        run: python scripts/arch_lint.py src/
      - name: Static Analysis
        run: ruff check src/ && mypy src/
      - name: Unit Tests
        run: pytest tests/unit -v --tb=short
      - name: Integration Tests
        run: pytest tests/integration -v --tb=short
      - name: Evals + Coverage
        run: pytest tests/evals -v --cov=src --cov-fail-under=80
```

## Production Deployment Architecture (from FlowIsle)

### Minimal Deployable Architecture

```
Web/CLI Client
    │
    ▼
API Gateway (鉴权 / 限流 / 会话)
    │
    ▼
Agent Orchestrator
├─ Planner (任务分解)
├─ Executor (工具调用)
├─ Policy Engine (权限决策)
└─ Context Manager (压缩/恢复)
    │
├─ Tool Runtime (Read/Edit/Bash/Web/MCP)
├─ Queue (重任务异步化)
├─ State Store (会话与检查点)
└─ Telemetry (日志/指标/追踪)
```

### Recommended Project Layout (Monorepo)

```
agent-platform/
├─ apps/
│  ├─ api/          # HTTP interface
│  ├─ worker/       # Async task execution
│  └─ cli/          # Local debugging entry
├─ packages/
│  ├─ orchestrator/ # Agent Loop & scheduling
│  ├─ tools/        # Tool contracts & implementations
│  ├─ policy/       # Permissions & rule engine
│  ├─ context/      # Compression & recovery
│  └─ observability/# Metrics & tracing
└─ infra/
   ├─ docker-compose.yml
   └─ k8s/
```

### Production Deployment Key Points

1. **Auth & tenant isolation**: Each organization gets independent policy and log spaces
2. **Tool sandboxing**: Command execution and file writes isolated, network egress restricted
3. **Quota system**: Per-user/project budgets for tokens, concurrency, and duration
4. **Canary releases**: New tools and policies deployed to canary first, observe before full rollout
5. **Audit trail**: All high-risk tool calls must be traceable

## Performance Optimization Patterns (from FlowIsle)

### 1. Tool Order Stability for Cache Hits

```python
# BAD: Unstable ordering defeats caching
tools = sorted(all_tools, key=lambda t: t.name)

# GOOD: Built-in tools fixed order, dynamic tools sorted locally
builtin_tools = [ReadTool(), WriteTool(), BashTool()]  # Fixed order
dynamic_tools = sorted(mcp_tools, key=lambda t: t.name)
tools = builtin_tools + dynamic_tools
```

### 2. Semantic Concurrency Batching

```python
import asyncio
from typing import TypeVar

T = TypeVar("T")

async def execute_tools_with_concurrency(
    calls: list[ToolCall],
    max_parallel: int = 3,
) -> list[ToolResult]:
    """Read-only tools in parallel, side-effect tools serialized."""
    results: list[ToolResult] = []

    read_calls = [c for c in calls if c.tool.risk_level == ToolRisk.READ_ONLY]
    write_calls = [c for c in calls if c.tool.risk_level != ToolRisk.READ_ONLY]

    # Batch read-only calls
    for i in range(0, len(read_calls), max_parallel):
        batch = read_calls[i:i + max_parallel]
        batch_results = await asyncio.gather(
            *(call.tool.execute(call.input, call.context) for call in batch)
        )
        results.extend(batch_results)

    # Serialize write/destructive calls
    for call in write_calls:
        result = await call.tool.execute(call.input, call.context)
        results.append(result)

    return results
```

### 3. Selective Recovery After Compression

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CompactedContext:
    """After compression, restore only critical context."""
    summary: str
    key_files: tuple[str, ...]  # Recently used files
    active_rules: tuple[str, ...]  # Invariant rules

    @classmethod
    def from_full_context(cls, messages: list[dict],
                          file_cache: dict[str, str],
                          n_key_files: int = 5) -> "CompactedContext":
        # Summarize old messages
        summary = _summarize(messages[:-10])
        # Keep most recently used files
        recent = sorted(file_cache.keys(), key=lambda k: file_cache[k], reverse=True)
        key_files = tuple(recent[:n_key_files])
        # System rules always survive compression
        rules = ("dependency_direction", "no_bare_except", "type_annotations_required")
        return cls(summary=summary, key_files=key_files, active_rules=rules)
```

## Hook Mechanism (from FlowIsle)

Hooks are feedback loops, not decorations. They insert validation and policy at critical nodes:

| Hook Event | Purpose |
|-----------|---------|
| `PreToolUse` | Validate input before tool executes |
| `PostToolUse` | Verify output, log result |
| `PermissionRequest` | Route to approval workflow |
| `PreCompact` | Save invariants before compression |
| `PostCompact` | Restore invariants after compression |
| `SessionStart` | Load project context and rules |
| `SessionEnd` | Persist state and metrics |

```python
from typing import Callable
from dataclasses import dataclass, field


@dataclass
class HookRegistry:
    _hooks: dict[str, list[Callable]] = field(default_factory=dict)

    def register(self, event: str, handler: Callable) -> None:
        self._hooks.setdefault(event, []).append(handler)

    async def fire(self, event: str, context: dict) -> dict:
        for handler in self._hooks.get(event, []):
            context = await handler(context)
        return context

# Usage
registry = HookRegistry()

registry.register("PreToolUse", validate_input_schema)
registry.register("PreToolUse", check_permission)
registry.register("PostToolUse", log_tool_result)
registry.register("PreCompact", save_invariants)
```

## Daily Operations Rhythm (from FlowIsle)

Practical suggestion for team daily workflow:

- **Morning**: Batch process high-certainty tasks (refactoring, migration, batch fixes)
- **Afternoon**: Medium-certainty tasks (new features, API integration)
- **Evening**: Run regression suite and cost review (token usage, failure rate, recovery count)

## Agent Loop State Management (from FlowIsle)

```python
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class LoopState(str, Enum):
    RUNNING = "running"
    COMPACTING = "compacting"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentLoopConfig:
    max_iterations: int = 50
    max_recovery_attempts: int = 1  # Each recovery type: try once only
    context_budget_threshold: float = 0.4  # Trigger compaction at 40%
    timeout_seconds: float = 300.0


@dataclass
class AgentLoopState:
    config: AgentLoopConfig
    iteration: int = 0
    recovery_count: int = 0
    state_transitions: list[str] = field(default_factory=list)

    def record_transition(self, reason: str) -> None:
        self.state_transitions.append(f"iter={self.iteration}: {reason}")
        logger.info("state_transition", iteration=self.iteration, reason=reason)
```

## Tool Contract Protocol

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeVar, Generic
from pydantic import BaseModel

T_Input = TypeVar("T_Input", bound=BaseModel)
T_Output = TypeVar("T_Output", bound=BaseModel)


class ToolRisk(str, Enum):
    READ_ONLY = "read_only"
    IDEMPOTENT = "idempotent"
    DESTRUCTIVE = "destructive"


class ConcurrencySafety(str, Enum):
    SAFE = "safe"         # Can run in parallel
    UNSAFE = "unsafe"     # Must serialize


class ToolContract(Protocol, Generic[T_Input, T_Output]):
    """Every tool must implement this contract."""

    @property
    def input_schema(self) -> type[T_Input]: ...

    @property
    def risk_level(self) -> ToolRisk: ...

    @property
    def concurrency(self) -> ConcurrencySafety: ...

    def check_permissions(self, input_data: T_Input, context: dict) -> bool: ...

    async def execute(self, input_data: T_Input, context: dict) -> T_Output: ...
```

## Context Budget Configuration

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ContextBudget:
    max_tokens: int = 100_000
    warning_threshold: float = 0.4
    compact_threshold: float = 0.6
    collapse_threshold: float = 0.8
    autocompact_threshold: float = 0.9
    # Invariants that survive any compression
    system_invariants: tuple[str, ...] = (
        "project_rules",
        "tool_boundaries",
        "session_constraints",
    )
```

## Recovery Checkpoint Pattern

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    task_id: str
    iteration: int
    completed_actions: tuple[str, ...]
    timestamp: float

    def can_resume_from(self, failed_iteration: int) -> bool:
        return self.iteration <= failed_iteration
```

## Deployment Priorities (P0/P1/P2)

### P0: 先把系统拉到"可控"

- 建立上下文预算阈值（监控 40% 利用率拐点）
- 给每个工具补齐 只读/破坏性/并发安全 语义标签
- 把权限判断迁移到代码路径强制执行（不要只靠提示词）

### P1: 把"可控"升级为"可持续"

- 上线分层记忆与老化策略（项目/会话/团队）
- 上线自动压缩 + 恢复边界
- 建立可观测闭环（Token、成本、时延、失败率、关键事件）

### P2: 把"可持续"升级为"可规模化"

- 引入协调者-执行者多 Agent 架构
- 建立失败回滚纪律（失败先回滚，而非硬修补）
- 定期做 Harness 减法，降低系统复杂度债务

## Team Roles & Workflow

### 角色分工

- **Harness Owner**: 维护策略、权限、观测指标
- **Feature Owner**: 定义业务验收标准与边界
- **Reviewer**: 审核高风险调用与关键改动

### 单任务工作流（标准版）

1. **任务定义** — 输入目标、边界、验收标准
2. **任务分解** — Planner 拆成可执行子任务
3. **策略编译** — 给每个子任务绑定工具与权限范围
4. **执行阶段** — Executor 调工具，实时回填中间结果
5. **验证阶段** — 自动跑 lint/test/build 与策略校验
6. **收敛阶段** — 输出结果 + 风险说明 + 下一步建议
7. **归档复盘** — 记录失败点，沉淀成下一版策略


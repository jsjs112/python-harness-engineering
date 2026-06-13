---
name: python-harness-engineering
version: 2.0.0
description: >
  Python Harness Engineering — 让 AI Agent 在严格工程约束下稳定执行。
  六层架构 + 依赖方向强制 + stability gate 质量门禁 + 失败回退机制。
tags: [python, architecture, quality-gate, agent-friendly, harness, stability, engineering]
trigger_keywords:
  - harness engineering
  - agent-friendly code
  - 六层架构
  - 依赖方向
  - stability gate
  - 质量门禁
  - arch_lint
  - 开发规范
  - Python 项目结构
  - 工程约束
  - 稳定性优先
when_to_use: >
  当用户需要：创建新的 Python 项目、重构代码为 agent 友好结构、
  建立架构规则（依赖方向、层边界）、设置质量门禁（stability gate）、
  制定开发工作流标准（spec-first、validate-before-merge）、
  或对项目进行 harness 工程审计时使用。
---

# Python Harness Engineering

> "Humans steer, agents execute." Harness Engineering 不是让 AI 更聪明，而是让 AI 在严格的工程约束下稳定、可预测地执行。

## When to Activate

Apply this skill when:
- Creating a new Python project intended for AI agent collaboration
- Refactoring an existing Python codebase to be agent-friendly
- Setting up architecture enforcement rules (dependency direction, layer boundaries)
- Defining quality gates and stability checks for automated development
- Establishing development workflow standards (spec-first, validate-before-merge)
- Auditing a project for harness engineering anti-patterns

## TL;DR — 三步走

```
Step 1: SCAFFOLD  → 创建项目结构 + AGENTS.md + RULES.md + pyproject.toml
Step 2: IMPLEMENT → 在六层架构约束下编码，每个模块写完立刻 arch_lint 验证
Step 3: GATE      → python scripts/stability_gate.py 全过才能合并
```

如果只记住一件事：**没有通过 stability gate 的代码，不允许合并。**

## Quick Start — 30 秒上手

### 方式 A: 一键脚手架（推荐）

```bash
# 一条命令创建完整项目结构（含 conftest.py、示例测试、所有脚本）
python scripts/harness_init.py <package_name> --output-dir <parent-dir>

# 示例: 创建 order_system 项目
python scripts/harness_init.py order_system --output-dir ~/projects

# 创建后进入项目并安装依赖
cd ~/projects/order_system
pip install -e ".[dev]"
python scripts/stability_gate.py --dry-run   # 预览将执行的检查
python scripts/harness_audit.py              # 查看项目健康度
```

> `harness_init.py` 会自动：创建六层目录结构、复制 AGENTS.md/RULES.md/pyproject.toml、生成三级 conftest.py（含 fixture 模板）、复制 arch_lint/stability_gate/harness_audit 脚本、创建示例测试文件。

### 方式 B: 手动搭建

**macOS / Linux:**
```bash
# Step 1: 复制模板到项目根目录
cp templates/AGENTS.md  <project-root>/AGENTS.md
cp templates/RULES.md   <project-root>/RULES.md
cp templates/pyproject.toml <project-root>/pyproject.toml

# Step 2: 创建标准目录结构
mkdir -p src/<package_name>/{repository,service,api,runtime}
mkdir -p tests/{unit,integration,evals}
mkdir -p scripts docs
touch src/<package_name>/__init__.py
touch src/<package_name>/types.py
touch src/<package_name>/config.py

# Step 2b: 创建测试 __init__.py 和 conftest.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py tests/evals/__init__.py
cp templates/conftest_root.py         <project-root>/tests/conftest.py
cp templates/conftest_unit.py         <project-root>/tests/unit/conftest.py
cp templates/conftest_integration.py  <project-root>/tests/integration/conftest.py
cp templates/conftest_evals.py        <project-root>/tests/evals/conftest.py

# Step 3: 复制工具脚本
cp scripts/arch_lint.py      <project-root>/scripts/
cp scripts/stability_gate.py <project-root>/scripts/
cp scripts/harness_audit.py  <project-root>/scripts/
cp scripts/harness_init.py   <project-root>/scripts/

# Step 4: 安装开发依赖并验证
pip install -e ".[dev]"
python scripts/stability_gate.py --dry-run   # 预览将执行的检查
python scripts/harness_audit.py              # 查看项目健康度
```

**Windows (PowerShell):**
```powershell
# Step 1: 复制模板
Copy-Item templates\AGENTS.md, templates\RULES.md, templates\pyproject.toml <project-root>\

# Step 2: 创建标准目录结构
New-Item -ItemType Directory -Force -Path src\<package_name>\repository, src\<package_name>\service, src\<package_name>\api, src\<package_name>\runtime
New-Item -ItemType Directory -Force -Path tests\unit, tests\integration, tests\evals, scripts, docs
New-Item -ItemType File -Force -Path src\<package_name>\__init__.py, src\<package_name>\types.py, src\<package_name>\config.py

# Step 2b: 创建测试 conftest.py
New-Item -ItemType File -Force -Path tests\__init__.py, tests\unit\__init__.py, tests\integration\__init__.py, tests\evals\__init__.py
Copy-Item templates\conftest_root.py <project-root>\tests\conftest.py
Copy-Item templates\conftest_unit.py <project-root>\tests\unit\conftest.py
Copy-Item templates\conftest_integration.py <project-root>\tests\integration\conftest.py
Copy-Item templates\conftest_evals.py <project-root>\tests\evals\conftest.py

# Step 3: 复制工具脚本
Copy-Item scripts\arch_lint.py, scripts\stability_gate.py, scripts\harness_audit.py, scripts\harness_init.py <project-root>\scripts\

# Step 4: 安装开发依赖并验证
pip install -e ".[dev]"
python scripts\stability_gate.py --dry-run
python scripts\harness_audit.py
```

> **提示**: 将 `<project-root>` 替换为你的实际项目路径，`<package_name>` 替换为包名（如 `order_system`）。

## Document Map — 该读什么文件

```
你要做什么？                            → 读哪个文件
────────────────────────────────────────────────────────────
第一次搭建项目                            → 本文件 Quick Start（推荐用 harness_init.py 一键生成）
手动搭建项目                              → 本文件 Quick Start > 方式 B
写代码时查规则                            → RULES.md（项目根目录）
了解项目结构和入口                         → AGENTS.md（项目根目录）
写测试 / 不知道 fixture 怎么写             → templates/conftest_root.py + conftest_unit.py
写集成测试 / eval 测试                     → templates/conftest_integration.py + conftest_evals.py
查看完整的六层代码示例                      → reference-architecture.md
查看 CI/CD 集成示例                       → reference-architecture.md #ci/cd-integration
查看部署架构和多 Agent 设计                → reference-architecture.md #production-deployment
配置 ruff/mypy/pytest                     → templates/pyproject.toml
了解常见反模式                            → 本文件 Anti-Patterns 表格
失败恢复 / 检查点回退                      → 本文件 Recovery Integration 章节
```

## Core Philosophy

**Agent = Model + Harness.** 模型是 CPU，Harness 是操作系统。CPU 再强，没有调度、内存、权限和故障恢复，系统依然不可用。

Three axioms:

1. **约束即倍增器** — 每增加一条明确约束，agent 的可靠性成倍提升
2. **沉默即成功** — 好的 harness 不需要 agent 理解它，只需要无法违反它
3. **环境大于模型** — 与其优化 prompt，不如优化 agent 工作的环境

### 概念嵌套关系（别把它们并列）

Prompt Engineering、Context Engineering、Harness Engineering 不是三件并列的事，而是嵌套关系：

```
Prompt Engineering ⊂ Context Engineering ⊂ Harness Engineering
```

- **Prompt Engineering**：怎么说（表达层）— 决定指令质量
- **Context Engineering**：给模型看什么（信息层）— 决定信息质量
- **Harness Engineering**：系统怎么运行、怎么约束、怎么恢复（执行层）— 决定系统质量

Prompt 优化的是单次指令，Context 优化的是单次信息输入，Harness 优化的是整个执行系统的可靠性。

## Project Structure (Standard Layout)

Every harness-engineered Python project MUST follow this directory layout:

```
project-root/
├── AGENTS.md             # Agent navigation: what this project is, how to work with it
├── RULES.md              # Machine-enforceable rules and constraints
├── pyproject.toml        # Project config with tool configs (ruff, mypy, pytest)
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── types.py      # Layer 0: Pure data types, no imports from other layers
│       ├── config.py     # Layer 1: Configuration, imports only from types
│       ├── repository/   # Layer 2: Data access, imports from types + config
│       ├── service/      # Layer 3: Business logic, imports from types + config + repository
│       ├── api/          # Layer 4: Interface layer, imports from all below
│       └── runtime/      # Layer 5: Orchestration, DI, imports from all
├── tests/
│   ├── conftest.py       # Shared fixtures (app_config, structlog reset, tmp_data_dir)
│   ├── unit/
│   │   └── conftest.py   # Fake repos, mocked deps, builder helpers
│   ├── integration/
│   │   └── conftest.py   # Real DB, session factory, rollback isolation
│   └── evals/
│       └── conftest.py   # Production-like config, capability fixtures
├── scripts/
│   ├── arch_lint.py      # Architecture dependency checker
│   ├── stability_gate.py # Pre-merge quality gate
│   ├── harness_audit.py  # Harness health audit
│   └── harness_init.py   # Project scaffolding (one-command setup)
└── docs/
    └── architecture.md   # (Optional) Human-readable ADRs: why you chose each layer's tech stack
```

### Dependency Direction Rule

```
types → config → repository → service → api → runtime
  0        1          2           3        4       5

ONLY lower-numbered layers may be imported by higher-numbered layers.
Reverse imports are CRITICAL violations.
```

## AGENTS.md Template

Every project MUST have an `AGENTS.md` at the root. This is the agent's entry point.

```markdown
# Project: [name]

## Purpose
[One sentence: what this project does]

## Architecture
[3-5 sentences: layered structure, key design decisions]

## Development Workflow
1. Read RULES.md before making any changes
2. Write tests BEFORE modifying implementation
3. Run `python scripts/stability_gate.py` before committing
4. All changes must pass `ruff check && mypy src/ && pytest`

## Key Entry Points
- Main: `src/package_name/runtime/app.py`
- API: `src/package_name/api/`
- Config: `src/package_name/config.py`

## Forbidden Actions
- Never modify types.py without updating all dependent layers
- Never add cross-layer imports that violate dependency direction
- Never skip the stability gate check
```

For the full template, see [templates/AGENTS.md](templates/AGENTS.md).

## RULES.md Design

RULES.md encodes constraints in a format that is both human-readable and machine-checkable.

```markdown
# Rules

## R001: Dependency Direction
Layers must only import from lower-numbered layers.
Enforced by: `python scripts/arch_lint.py`

## R002: No Bare Excepts
All exception handling must catch specific exception types.
Enforced by: ruff rule E722

## R003: Type Annotations Required
All public function signatures must have complete type annotations.
Enforced by: `mypy --strict src/`

## R004: Test Before Merge
Every change must include tests. Coverage must not decrease.
Enforced by: `pytest --cov=src --cov-fail-under=80`

## R005: No Mutable Defaults
Function parameters must not use mutable default values.
Enforced by: ruff rule B006

## R006: Structured Logging Only
Use `structlog` for all logging. No `print()` statements in src/.
Enforced by: ruff custom rule + arch_lint.py
```

For the full template, see [templates/RULES.md](templates/RULES.md).

## Stability-First Development Workflow

### Phase 1: Spec Before Code

Before writing ANY implementation:

1. Define the change intent in natural language (what, not how)
2. Write the test that validates the change (RED phase)
3. Define success criteria (pass/fail conditions)
4. Run `python scripts/stability_gate.py --dry-run` to preview what will be checked

**CHECKPOINT — Phase 1 Gate:**
```
测试能运行吗？
├─ YES → 测试 FAIL 了吗？（应该 FAIL，因为还没实现）
│         ├─ YES → 通过，进入 Phase 2
│         └─ NO  → 需求定义可能太宽泛，拆分后重新写测试
└─ NO  → 需求定义不清楚 → 回到第 1 步，明确输入/输出/边界
         还是写不出来？→ 用最简单的 assert + expected output 先覆盖
```

#### Failure Fallback — Phase 1

| Trigger | First-Line Fix | Still Fails → Fallback |
|---------|---------------|----------------------|
| 写不出测试 | 拆分需求为更小的单元 | 用最简单的 assert + expected output 先覆盖 |
| `--dry-run` 报错 | 检查 pyproject.toml 是否配置了 pytest | 手动列出需要执行的检查项 |
| 需求定义模糊 | 追问用户：输入是什么？输出是什么？边界在哪？ | 用假设写注释，标记 `# ASSUMPTION:` 待确认 |

### Phase 2: Constrained Implementation

During implementation:

1. Follow the dependency direction strictly
2. Add type annotations to every public symbol
3. Use structured logging (`structlog`) for observability
4. Keep functions under 30 lines; classes under 200 lines
5. No `print()`, no `import *`, no bare `except`

**CHECKPOINT — Phase 2 Gate:**
```
python scripts/arch_lint.py src/  输出什么？
├─ OK（0 violations）→ 继续写下一个模块
└─ violations found → 违规类型是什么？
                      ├─ 循环导入 → 把共享类型移到 types.py（Layer 0）
                      ├─ 反向导入 → 移动 import 到正确的层
                      └─ 不确定   → 引入 Protocol 接口在 types.py 解耦
                                    修复后重新运行 arch_lint.py
```

#### Failure Fallback — Phase 2

| Trigger | First-Line Fix | Still Fails → Fallback |
|---------|---------------|----------------------|
| arch_lint.py 报循环导入 | 把共享类型移到 types.py（Layer 0） | 引入 Protocol 接口解耦 |
| mypy 类型推导失败 | 添加显式 TypeAlias 或 cast() | 对该函数添加 `# type: ignore[specific-error]` 并记录 TODO |
| 函数超过 30 行 | 提取私有辅助函数 | 如果逻辑确实不可分，添加注释说明原因 |
| structlog import 失败 | `pip install structlog` 并更新 pyproject.toml | 用 logging 标准库 + JSON formatter 替代 |

### Phase 3: Validate Before Merge

Before committing:

```bash
# Run the full stability gate
python scripts/stability_gate.py

# This executes (in order, fail-fast):
# 1. arch_lint.py       - Architecture dependency check
# 2. ruff check src/    - Lint and style
# 3. mypy src/          - Type safety
# 4. pytest tests/unit  - Unit tests
# 5. pytest tests/integration  - Integration tests
# 6. pytest tests/evals --cov=src --cov-fail-under=80  - Evals + coverage
```

If ANY gate fails, the change MUST NOT be merged.

**CHECKPOINT — Phase 3 Gate:**
```
python scripts/stability_gate.py 输出什么？
├─ CLEAR（all passed）→ 可以合并
└─ BLOCKED → 哪个 gate 失败了？
             ├─ arch_lint   → 检查 import 方向，移动导入到正确的层
             ├─ ruff        → 运行 ruff check src/ --fix 自动修复
             ├─ mypy        → 添加缺失的类型注解
             ├─ unit tests  → pytest --pdb 调试，修复代码或测试
             ├─ integration → 检查外部依赖是否可用，用 mock 隔离
             └─ coverage    → 补充测试用例（critical path 必须 100%）
             修复后重新运行 stability_gate.py
```

#### Failure Fallback — Phase 3

| Gate Fails | First-Line Fix | Still Fails → Fallback |
|------------|---------------|----------------------|
| arch_lint.py (R001) | 检查 import 方向，移动导入到正确的层 | 引入 Protocol 在 types.py 解耦 |
| ruff check | 运行 `ruff check src/ --fix` 自动修复 | 逐条阅读错误，手动修复不可自动修复的 |
| mypy | 添加缺失的类型注解 | 对第三方库无 stub 的情况添加 `# type: ignore[import-untyped]` |
| pytest unit | 读失败输出，修复被测代码或修正测试 | 用 `pytest --pdb` 进入调试模式逐步排查 |
| pytest integration | 检查外部依赖（数据库、API）是否可用 | 用 mock 隔离外部依赖，单独测试集成逻辑 |
| coverage < 80% | 补充缺失的测试用例 | 降低非关键路径覆盖率到 60%，但 critical path 保持 100% |

### Recovery Integration — 何时调用检查点恢复

每个 Phase 的 Fallback 表是"就地修复"策略。当就地修复也失败时，应调用检查点恢复，从最近的成功边界继续，而不是整个任务重来。

```
触发条件                          → 恢复策略
───────────────────────────────────────────────────────
Phase 1 反复失败（≥3 轮需求拆分仍写不出测试）
                                 → 回退到上一个已完成任务的检查点
                                   将当前任务标记为 BLOCKED，请求人工介入

Phase 2 arch_lint 修复引入新违规  → 恢复到本次修改前的 git 状态
（修复 A 导致 B 出现）              git checkout -- <file>
                                   然后重新审视依赖方向，用 Protocol 在 Layer 0 解耦

Phase 3 stability_gate 连续 2 次  → 恢复到 Phase 2 开始时（git stash）
同一 gate 失败                      检查是否修改了 types.py 导致级联影响
                                   如果 types.py 被改动，从 types.py 开始逐层验证

任意 Phase 超时（>5 分钟无进展）   → 记录当前进度为检查点
                                   回退到上一个通过 CHECKPOINT 的 Phase
                                   输出诊断信息，请求人工决策
```

> **原则**：失败先回滚，而非硬修补。回滚不丢信息（检查点保存了进度），硬修补可能越改越乱。

## Constraint Enforcement

### Architecture Linting

Use `scripts/arch_lint.py` to enforce dependency direction:

```bash
python scripts/arch_lint.py src/
```

The script checks every import statement and reports violations. Exit code 0 = clean, 1 = violations found.

### Static Analysis Stack

Required tool configs in `pyproject.toml`: ruff (lint + style, enable rules E/F/W/I/N/UP/B/A/SIM/TCH), mypy (`strict = true`, `disallow_untyped_defs = true`), pytest (markers: slow/integration/eval).

For the full pyproject.toml template, see [templates/pyproject.toml](templates/pyproject.toml).

## Error Handling Pattern

Every module defines a local exception hierarchy using `@dataclass(frozen=True)` for structured error data.

### 最小可用模板

```python
from dataclasses import dataclass


class ServiceError(Exception):
    """Base error for service layer."""
    pass


@dataclass(frozen=True)
class ValidationError(ServiceError):
    field: str
    message: str
    value: object = None

    def __str__(self) -> str:
        return f"Validation failed on '{self.field}': {self.message}"


@dataclass(frozen=True)
class NotFoundError(ServiceError):
    entity: str
    identifier: str

    def __str__(self) -> str:
        return f"{self.entity} not found: {self.identifier}"
```

Rules for error handling:

1. **Never use bare `except`** — always catch specific exception types
2. **Use exception chaining** — `raise ServiceError(...) from original_error`
3. **Errors are data** — use `@dataclass(frozen=True)` for structured error info
4. **Log at boundaries** — catch and log at API/runtime layer, re-raise in service layer
5. **Recovery hints** — every error should suggest what to do next

> 完整的分层错误体系（types → repository → service → api）见 [reference-architecture.md](reference-architecture.md#error-hierarchy-pattern)。

## Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

def process_order(order_id: str) -> OrderResult:
    logger.info("processing_order", order_id=order_id, stage="start")
    try:
        result = _execute(order_id)
        logger.info("processing_order", order_id=order_id, stage="complete",
                     duration_ms=result.duration_ms)
        return result
    except ValidationError as e:
        logger.warning("processing_order_validation_failed",
                       order_id=order_id, field=e.field, message=e.message)
        raise
    except Exception as e:
        logger.error("processing_order_unexpected",
                     order_id=order_id, error_type=type(e).__name__,
                     error_message=str(e))
        raise
```

### Health Check Pattern

```python
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class HealthStatus:
    status: str  # "healthy" | "degraded" | "unhealthy"
    checks: dict[str, bool] = field(default_factory=dict)
    version: str = "0.1.0"


def health_check(
    dependencies: dict[str, Callable[[], bool]],
    version: str = "0.1.0",
) -> HealthStatus:
    """Each dependency reports True=ok, False=failed.
    Any single failure = degraded; all failures = unhealthy."""
    checks = {name: check_fn() for name, check_fn in dependencies.items()}
    failures = sum(1 for ok in checks.values() if not ok)
    if failures == 0:
        status = "healthy"
    elif failures < len(checks):
        status = "degraded"
    else:
        status = "unhealthy"
    return HealthStatus(status=status, checks=checks, version=version)


# Usage:
# result = health_check({
#     "database": lambda: db.ping(),
#     "cache": lambda: cache.ping(),
#     "queue": lambda: queue.ping(),
# })
```

## Agent Loop Anti-Runaway Design

Agent Loop 是系统心跳，不是"单次问答"。生产系统必须先承认失败是常态，再设计恢复主路径。

Five anti-runaway rules:

1. **每类自动恢复仅尝试一次** — 防止无限重试
2. **压缩策略分层触发** — 从轻压缩到重压缩逐级升级
3. **错误优先内部恢复** — 最后才向上抛出
4. **每次状态迁移记录原因** — 便于回放和断言
5. **设置硬性超时与循环上限** — 兜底保护

### 最小可用实现（直接复制使用）

```python
from dataclasses import dataclass, field
from enum import Enum


class LoopState(str, Enum):
    RUNNING = "running"
    COMPACTING = "compacting"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentLoopConfig:
    max_iterations: int = 50
    max_recovery_attempts: int = 1      # 每种恢复类型只尝试一次
    context_budget_threshold: float = 0.4  # 40% 利用率触发压缩
    timeout_seconds: float = 300.0


@dataclass
class AgentLoopState:
    config: AgentLoopConfig
    iteration: int = 0
    recovery_count: int = 0
    state_transitions: list[str] = field(default_factory=list)

    def record_transition(self, reason: str) -> None:
        self.state_transitions.append(f"iter={self.iteration}: {reason}")

    def should_continue(self) -> bool:
        """Check all stop conditions: iteration cap, recovery cap, timeout."""
        if self.iteration >= self.config.max_iterations:
            return False
        if self.recovery_count >= self.config.max_recovery_attempts:
            return False
        return True
```

> 完整的生产级实现（含 Hook 机制、Tool Contract Protocol、Context Budget 四级压缩）见 [reference-architecture.md](reference-architecture.md)。

## Tool Contract Pattern

把"会调用"升级为"可验证调用"。每个工具必须实现以下契约：

- **Schema-first**: 参数先用 Pydantic 校验，减少"模型胡传参数"导致的运行时故障
- **语义标签**: 调度器可推断并发与风险等级（read_only / idempotent / destructive）
- **权限内建**: 权限不是外挂，而是工具契约的一部分

Semantic concurrency rules:

| Tool Type | Concurrency | Example |
|-----------|-------------|---------|
| Read/Grep/Glob (read-only) | Parallel | File search, content read |
| Edit/Write (idempotent) | Serialize | File modification |
| Bash/Deploy (destructive) | Serialize + approval | Shell commands, deployments |

### ToolContract 最小实现

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Generic, TypeVar
from pydantic import BaseModel

T_Input = TypeVar("T_Input", bound=BaseModel)
T_Output = TypeVar("T_Output", bound=BaseModel)


class ToolRisk(str, Enum):
    READ_ONLY = "read_only"
    IDEMPOTENT = "idempotent"
    DESTRUCTIVE = "destructive"


class ToolContract(Protocol, Generic[T_Input, T_Output]):
    """每个工具必须实现的契约。"""

    @property
    def input_schema(self) -> type[T_Input]: ...
    @property
    def risk_level(self) -> ToolRisk: ...
    def check_permissions(self, input_data: T_Input, context: dict) -> bool: ...
    async def execute(self, input_data: T_Input, context: dict) -> T_Output: ...
```

> 完整实现（含 ConcurrencySafety、HookRegistry、权限路由）见 [reference-architecture.md](reference-architecture.md#tool-contract-protocol)。

## Context Budget Management

上下文是预算，不是仓库。压缩不是删历史，而是维持可推理状态。

Four-level compression strategy (从轻到重):

| Level | Strategy | When | Action |
|-------|----------|------|--------|
| 1 | **Snip** | 利用率 >40% | 裁剪最旧的消息 |
| 2 | **MicroCompact** | 利用率 >60% | 局部摘要工具输出 |
| 3 | **Collapse** | 利用率 >80% | 折叠大块工具输出 |
| 4 | **AutoCompact** | 利用率 >90% | 重建摘要上下文（最后手段） |

Key invariant: 系统不变量（项目规则、工具边界、会话约束）必须持续注入，避免压缩后"失忆"。

## Recovery-First Design

先承认失败是常态，再设计恢复主路径。核心思路：记录可恢复边界（检查点），中断后从最近可验证边界恢复，而不是整段任务重来。

### Checkpoint 最小实现

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


def recover_from_checkpoint(
    checkpoints: list[Checkpoint],
    failed_iteration: int,
) -> Checkpoint | None:
    """找到最近的可恢复检查点。"""
    valid = [cp for cp in checkpoints if cp.can_resume_from(failed_iteration)]
    return max(valid, key=lambda cp: cp.iteration) if valid else None
```

> 完整的检查点持久化 + 恢复流程见 [reference-architecture.md](reference-architecture.md)。

## Effectiveness Metrics

衡量 Harness 是否有效的 5 个核心指标：

| Metric | Target | Meaning |
|--------|--------|---------|
| 任务一次完成率 | 越高越好 | 系统可靠性 |
| 平均恢复次数 | 越低越好 | 失败恢复效率 |
| 单任务 token 成本 | 持续优化 | 资源效率 |
| 高风险调用占比 | 越低越好 | 安全控制 |
| 回归失败率 | 趋近 0% | 变更稳定性 |

如果这 5 个指标持续变好，说明 Harness 正在产生真实工程收益。

> 部署优先级 (P0/P1/P2)、团队角色分工、多 Agent 工作流等进阶内容见 [reference-architecture.md](reference-architecture.md#production-deployment)。

## Testing Strategy

### Three-Tier Testing

| Tier | Purpose | Location | When to Run | Fixture Template |
|------|---------|----------|-------------|-----------------|
| Unit | Verify isolated logic | `tests/unit/` | Every change | `templates/conftest_unit.py` — fake repos, no I/O |
| Integration | Verify component interaction | `tests/integration/` | Every change | `templates/conftest_integration.py` — real DB, rollback isolation |
| Eval | Verify agent-facing capability | `tests/evals/` | Pre-merge | `templates/conftest_evals.py` — production-like config |

> 所有层级共享 `templates/conftest_root.py`（structlog 清理、app_config、tmp_data_dir）。
> `harness_init.py` 会自动将 conftest 模板复制到正确位置并替换包名。

### Eval-Driven Development

Define expected behavior BEFORE implementation:

```python
# tests/evals/test_order_processing.py
import pytest


@pytest.mark.eval
class TestOrderProcessingCapability:
    """Capability eval: order processing must handle standard workflows."""

    def test_creates_order_with_valid_input(self, order_service):
        order = order_service.create(user_id="u1", items=[("SKU001", 2)])
        assert order.status == "created"
        assert order.total > 0

    def test_rejects_empty_items(self, order_service):
        with pytest.raises(ValidationError, match="items.*non-empty"):
            order_service.create(user_id="u1", items=[])

    def test_idempotent_creation(self, order_service):
        """Same request twice should not create duplicate orders."""
        order1 = order_service.create(user_id="u1", items=[("SKU001", 1)], idempotency_key="k1")
        order2 = order_service.create(user_id="u1", items=[("SKU001", 1)], idempotency_key="k1")
        assert order1.id == order2.id
```

### Coverage Requirements

- **Default**: 80% minimum line coverage
- **Critical paths** (payment, auth, data mutation): 100% branch coverage
- **Coverage must not decrease** on any merge

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| Prompt-only control | Prompts are suggestions, not constraints | Use RULES.md + automated enforcement |
| Circular imports | Creates fragile dependency chains | Enforce strict layer direction |
| Catch-all except | Silently swallows bugs | Catch specific types, chain with `from` |
| No stability gate | Broken code reaches main branch | Run `stability_gate.py` before every merge |
| Mutable defaults | Shared state between calls | Use `None` + factory pattern |
| Print debugging | No structure, no searchability | Use `structlog` with context fields |
| Missing AGENTS.md | Agent has no project context | Create and maintain AGENTS.md |
| Ignoring eval results | Capability regressions go unnoticed | Treat eval failures as CRITICAL blocks |
| God classes (>200 lines) | Agent loses context in large files | Split by responsibility |
| Untyped public APIs | Agent cannot infer signatures | `mypy --strict` on all public symbols |
| 只优化 Prompt 不治理工具与权限 | Prompt 是建议，权限是约束 | 工具语义标签 + 代码路径权限强制 |
| 默认全量上下文 | 等爆了再救火已晚 | 分级压缩策略 + 预算阈值 |
| 把并发当性能捷径 | 副作用工具并发导致数据竞争 | Read 并发、Write 串行、Destructive 审批 |
| Hook 写成万能脚本 | 失去边界与可维护性 | Hook 只做校验与策略，不做业务逻辑 |
| 没有恢复路径 | 所有异常都靠"重试碰碰运气" | 检查点 + 恢复边界 + 失败先回滚 |

## Quick Reference — 常用命令速查

```bash
# 初始化：一键创建完整项目（推荐）
harness-init:
  python scripts/harness_init.py <package_name> --output-dir <dir>
  # 自动创建：六层目录 + conftest.py + 示例测试 + 所有脚本 + AGENTS/RULES/pyproject

# 日常检查：每次改完代码跑一遍
harness-check:
  python scripts/arch_lint.py src/          # 架构依赖方向检查
  python -m ruff check src/                 # Lint + 风格
  python -m mypy src/                       # 类型安全

# 完整审计：项目健康度报告
harness-audit:
  python scripts/harness_audit.py <project-root>

# 合并门禁：所有检查必须通过
harness-gate:
  python scripts/stability_gate.py          # 完整质量门（fail-fast）
  python scripts/stability_gate.py --dry-run # 预览模式，不实际执行

# 单模块验证：写完一个模块立刻检查
  python scripts/arch_lint.py src/<pkg>/service/   # 只检查 service 层
  python scripts/arch_lint.py src/ --size-check     # 额外检查函数/类大小

# 测试运行：分层执行
  pytest tests/unit -v                      # 单元测试
  pytest tests/integration -v               # 集成测试
  pytest tests/evals -v --cov=src --cov-fail-under=80  # Eval + 覆盖率
```

## Additional Resources

- For detailed architecture patterns and layer design, see [reference-architecture.md](reference-architecture.md)
- For template files, see [templates/](templates/)
- For utility scripts, see [scripts/](scripts/)

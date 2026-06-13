# Python Harness Engineering

> **"Humans steer, agents execute."**
> Harness Engineering 不是让 AI 更聪明，而是让 AI 在严格的工程约束下稳定、可预测地执行。

一个 Skill，为 Python 项目提供 agent 友好的工程化框架：六层架构、依赖方向强制、质量门禁、三级测试脚手架，一条命令搭建完整项目。

---

## 核心理念

**Agent = Model + Harness.** 模型是 CPU，Harness 是操作系统。CPU 再强，没有调度、内存、权限和故障恢复，系统依然不可用。

```
Prompt Engineering ⊂ Context Engineering ⊂ Harness Engineering
```

- **Prompt Engineering** — 怎么说（表达层）
- **Context Engineering** — 给模型看什么（信息层）
- **Harness Engineering** — 系统怎么运行、怎么约束、怎么恢复（执行层）

## 快速开始

```bash
# 一条命令创建完整的 harness-engineered 项目
python scripts/harness_init.py order_system --output-dir ~/projects

# 预览模式（不实际创建）
python scripts/harness_init.py order_system --output-dir ~/projects --dry-run
```

`harness_init.py` 会自动生成：

```
order_system/
├── AGENTS.md                  # Agent 导航文档
├── RULES.md                   # 机器可执行的规则约束
├── pyproject.toml             # ruff + mypy + pytest 配置
├── src/order_system/
│   ├── types.py               # Layer 0: 纯数据类型
│   ├── config.py              # Layer 1: 配置
│   ├── repository/            # Layer 2: 数据访问
│   ├── service/               # Layer 3: 业务逻辑
│   ├── api/                   # Layer 4: 接口层
│   └── runtime/               # Layer 5: DI + 启动
├── tests/
│   ├── conftest.py            # 共享 fixture
│   ├── unit/conftest.py       # Fake repo, 零 I/O
│   ├── integration/conftest.py # 真实 DB + rollback 隔离
│   └── evals/conftest.py      # 生产级配置 + 能力测试
├── scripts/
│   ├── arch_lint.py           # 架构依赖检查
│   ├── stability_gate.py      # 合并前质量门禁
│   ├── harness_audit.py       # 项目健康度审计
│   └── harness_init.py        # 项目脚手架
└── docs/
```

创建后进入项目安装依赖：

```bash
cd ~/projects/order_system
pip install -e ".[dev]"
python scripts/stability_gate.py --dry-run   # 预览检查项
python scripts/harness_audit.py              # 查看健康度
```

## 六层架构

严格的依赖方向：**低层永远不能被高层反向导入。**

```
┌──────────────────────────────────────────────┐
│  Layer 5: Runtime     DI / 启动 / 生命周期     │
├──────────────────────────────────────────────┤
│  Layer 4: API         HTTP / gRPC / CLI       │
├──────────────────────────────────────────────┤
│  Layer 3: Service     业务逻辑 / 领域规则      │
├──────────────────────────────────────────────┤
│  Layer 2: Repository  数据访问 / ORM / 外部API │
├──────────────────────────────────────────────┤
│  Layer 1: Config      配置 / 环境变量 / 开关    │
├──────────────────────────────────────────────┤
│  Layer 0: Types       数据类 / 枚举 / Protocol │
└──────────────────────────────────────────────┘

依赖方向: types → config → repository → service → api → runtime
          只能从低编号层导入，反向导入 = CRITICAL 违规
```

## 工具脚本

### arch_lint.py — 架构依赖检查

用 AST 解析每个 import 语句，检测是否违反依赖方向。

```bash
python scripts/arch_lint.py src/                # 检查依赖方向
python scripts/arch_lint.py src/ --size-check   # 额外检查函数/类大小
```

### stability_gate.py — 合并前质量门禁

Fail-fast 级联检查，所有门禁必须通过才能合并。

```bash
python scripts/stability_gate.py            # 完整门禁
python scripts/stability_gate.py --dry-run  # 预览模式
```

执行顺序：arch_lint → ruff → mypy → unit tests → integration tests → evals + coverage。

### harness_audit.py — 项目健康度审计

检查项目结构、配置完整性、类型注解覆盖率，输出健康评分。

```bash
python scripts/harness_audit.py .           # 审计当前项目
```

### harness_init.py — 项目脚手架

一键创建完整的 harness-engineered 项目结构。

```bash
python scripts/harness_init.py <package_name> --output-dir <dir>
python scripts/harness_init.py <package_name> --dry-run  # 预览
```

## 开发工作流

```
Phase 1: Spec Before Code      → 先写测试，定义预期行为
Phase 2: Constrained Impl      → 在架构约束下编码，每个模块立刻 arch_lint
Phase 3: Validate Before Merge → stability_gate.py 全过才能合并
```

每个 Phase 都有结构化的 Checkpoint 决策树和 Failure Fallback 表。失败时的原则：**先回滚，而非硬修补。**

## 规则体系

RULES.md 编码了 10 条机器可执行的规则，每条都标注了严重级别和执行方式：

| 规则 | 严重级别 | 执行方式 |
|------|---------|---------|
| R001 依赖方向 | CRITICAL | arch_lint.py |
| R002 禁止裸 except | CRITICAL | ruff E722 |
| R003 类型注解 | HIGH | mypy --strict |
| R004 测试覆盖率 | CRITICAL | pytest --cov-fail-under=80 |
| R005 禁止可变默认值 | HIGH | ruff B006 |
| R006 结构化日志 | MEDIUM | ruff + arch_lint.py |
| R007 函数大小限制 | MEDIUM | arch_lint.py --size-check |
| R008 禁止通配导入 | HIGH | ruff F403 |
| R009 异常链 | MEDIUM | ruff B904 |
| R010 不可变数据类型 | MEDIUM | arch_lint.py |

## 三级测试

| 层级 | 目的 | Fixture 策略 |
|------|------|-------------|
| Unit | 验证隔离逻辑 | Fake repo，零 I/O，每个 test 独立实例 |
| Integration | 验证组件交互 | 真实 DB，session rollback 隔离 |
| Eval | 验证 agent 能力 | 生产级配置，module-scoped fixture |

## 文件说明

```
python-harness-engineering/
├── SKILL.md                    # Skill 主文件（工作流、规则、代码示例）
├── reference-architecture.md   # 参考架构（完整六层代码、CI/CD、部署）
├── README.md                   # 本文件
├── templates/
│   ├── AGENTS.md               # Agent 导航模板
│   ├── RULES.md                # 规则约束模板
│   ├── pyproject.toml          # 工具配置模板
│   ├── conftest_root.py        # 根级 conftest 模板
│   ├── conftest_unit.py        # 单元测试 conftest 模板
│   ├── conftest_integration.py # 集成测试 conftest 模板
│   └── conftest_evals.py       # 评估测试 conftest 模板
└── scripts/
    ├── arch_lint.py            # 架构依赖检查器
    ├── stability_gate.py       # 合并前质量门禁
    ├── harness_audit.py        # 项目健康度审计
    └── harness_init.py         # 项目脚手架
```



## 适用场景

- 从零搭建 AI Agent 会频繁修改的 Python 项目
- 重构已有代码为 agent 友好的分层结构
- 建立架构规则和自动化质量门禁
- 团队推行 spec-first + validate-before-merge 开发规范
- 对已有 Python 项目做 harness 工程健康审计

## 要求

- Python 3.11+
- pip（用于安装开发依赖）

## License

MIT

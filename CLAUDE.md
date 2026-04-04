# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目结构确认

确认我现在工作的目录：
- Pity 前端：/Users/zhanzhicai/Desktop/py/pity/frontend
- Pity 后端：/Users/zhanzhicai/Desktop/py/pity/backend
-
## Git 状态
前端 │ /Users/zhanzhicai/Desktop/py/pity/frontend │ feat/upgrade-plugin-system
后端 │ /Users/zhanzhicai/Desktop/py/pity/backend  │ feat/upgrade-plugin-system
分开提交：backend 和 frontend 单独 commit，只提交不推送

## 启动命令

```bash
python pity.py                                    # 启动后端服务 (0.0.0.0:7777)
uvicorn main:pity --reload                        # 开发模式热重载
alembic revision --autogenerate -m "描述"          # 生成数据库迁移
alembic upgrade head                              # 执行迁移
pip install -r requirements.txt                   # 安装依赖

# Celery Worker（独立终端）
celery -A celery_app worker --loglevel=info        # 启动 Worker 处理异步任务
celery -A celery_app flower --port=5555           # 启动 Flower 监控面板（可选）
celery -A celery_app beat --loglevel=info        # 启动 Beat 周期任务调度（可选）
```

环境变量 `pity_env=dev`（默认）读 `conf/dev.env`，`pity_env=pro` 读 `conf/pro.env`。

## 项目结构

```
backend/
├── main.py                 # 应用入口（定义 lifespan）
├── pity.py                 # 生产启动入口（uvicorn）
├── config.py               # 配置类（BaseConfig + DevConfig/ProConfig）
├── gunicorn.py             # Gunicorn 生产部署配置
├── alembic.ini             # Alembic 迁移配置
├── requirements.txt        # Python 依赖
├── conf/                   # 环境配置
│   ├── dev.env             # 开发环境（MySQL、Redis、OAuth 等）
│   └── pro.env             # 生产环境
├── celery_app.py          # Celery 应用配置（Phase 5）
├── app/
│   ├── routers/            # API 路由（按模块目录组织）
│   │   ├── auth/           # 认证（注册、登录、GitHub OAuth）
│   │   ├── project/        # 项目管理
│   │   ├── testcase/       # 测试用例
│   │   ├── config/         # 配置管理
│   │   ├── online/         # 在线工具（SQL、Redis）
│   │   ├── workspace/      # 工作空间
│   │   ├── oss/             # 对象存储
│   │   ├── notification/     # 消息通知
│   │   ├── operation/       # 操作日志
│   │   ├── scheduler/       # 任务调度（Phase 2）
│   ├── test_suite/       # 测试套件管理（Phase 3）
│   ├── task/            # Celery 异步任务（Phase 5）
│   └── request/         # HTTP 请求 / Mock 录制
│   ├── models/              # SQLAlchemy 数据模型
│   │   ├── basic.py         # PityBase 抽象基类
│   │   ├── scheduler.py      # 调度任务模型（Phase 2）
│   │   ├── test_suite.py     # 测试套件模型（Phase 3）
│   │   └── ...              # 其他业务模型
│   ├── crud/                # DAO 层（@ModelWrapper + @connect 模式）
│   │   ├── scheduler/        # 调度 DAO（Phase 2）
│   │   ├── test_suite/       # 测试套件 DAO（Phase 3）
│   │   └── ...              # 其他业务 DAO
│   ├── schema/              # Pydantic v2 验证模型（注意不是 schemas）
│   │   ├── scheduler.py      # 调度 Schema（Phase 2）
│   │   └── test_suite.py     # 测试套件 Schema（Phase 3）
│   └── ai_schema.py        # AI Schema（Phase 4）
│   ├── core/                # 核心业务逻辑（用例执行引擎、参数解析）
│   │   └── ai/              # AI 服务（Phase 4-5）
│   │       ├── base.py          # AI 服务基类
│   │       ├── openai_service.py # OpenAI/MiniMax API 实现
│   │       ├── graph/           # LangGraph 工作流（Phase 5）
│   │       │   ├── state.py     # 状态定义（TypedDict）
│   │       │   ├── nodes.py     # 节点定义（retrieval/generate/review）
│   │       │   └── builder.py   # 工作流构建器
│   │       └── prompt_template.py # Prompt 模板
│   ├── middleware/           # 中间件（CORS、错误处理、请求日志）
│   ├── utils/                # 工具函数（JWT、Redis、调度器等）
│   │   ├── scheduler.py      # 调度器核心（Phase 2）
│   │   └── suite_executor.py # 测试套件执行器（Phase 3）
│   └── tasks/                # Celery 异步任务（Phase 5）
│       └── ai_tasks.py       # AI 异步任务（生成、增强、批量）
│   ├── enums/                # 枚举类型
│   ├── exception/            # 自定义异常
│   └── handler/              # 处理器
├── statics/                  # 前端构建产物（生产部署）
├── templates/                # HTML 模板（测试报告）
├── logs/                     # 日志文件
└── alembic/                  # 数据库迁移脚本
```

## 架构概览

应用入口 `main.py` 定义 `lifespan` 上下文管理器，通过 `pity.router.lifespan_context = lifespan` 注册。启动时初始化：
1. Redis 连接
2. APScheduler 定时任务调度器（测试计划 cro，支持 MySQL 持久化），Celery异步任务(AI 生成)
3. 数据库自动建表

### 请求处理链

```
Request → CORS Middleware → Error Middleware → Router → DAO (@connect管理session) → Response
```

### 数据库层

- **Model**：
  - 非抽象模型：直接继承 `Base`，设置 `__tablename__`
  - 抽象基类：`PityBase`（`basic.py`），提供公共字段，不创建表
- **DAO**：`app/crud/__init__.py` 中的 `Mapper` 基类提供通用 CRUD，子类通过 `@ModelWrapper(Model)` 装饰器绑定模型
- **Session 管理**：`@connect` 装饰器自动获取/复用 `AsyncSession`，支持事务参数 `@connect(True)`
- **缓存**：`@RedisHelper.cache("dao")` 自动缓存查询结果，`@RedisHelper.up_cache("dao")` 写操作后自动清缓存

### 路由层

- 路由按模块组织在 `app/routers/` 下，每个模块的 `__init__.py` 汇聚子路由导出 `router`
- 认证：`Depends(Permission())` 从 `Authorization` Header 解析 JWT，`Permission(role=Config.ADMIN)` 可限定角色
- 响应统一通过 `PityResponse.success()` / `PityResponse.failed()` 返回 `{code, msg, data}` 格式

### 任务调度系统（Phase 2）

- **调度器**：`app/utils/scheduler.py` 封装 APScheduler
- **持久化**：使用 `SQLAlchemyJobStore` 将任务存储在 MySQL 的 `apscheduler_jobs` 表
- **任务类型**：支持 `http`、`sql`、`redis`、`python`、`testcase`、`test_plan`
- **执行记录**：`PityTaskExecution` 模型记录每次执行的开始/结束时间、状态、结果

### Celery 异步任务系统（Phase 5）

Celery 与 APScheduler 互补：APScheduler 处理**定时/周期**任务（cron），Celery 处理**异步/排队**任务（队列）。

- **Celery 应用**：`celery_app.py` 配置 broker/backend 为 Redis
- **任务定义**：`app/tasks/ai_tasks.py`，包含 `generate_testcase`、`enhance_asserts`、`batch_generate`
- **任务状态查询**：
  - `GET /task/{task_id}` — 查询任务状态
  - `GET /task/{task_id}/result` — 获取任务结果
- **异步 AI 端点**（`app/routers/testcase/ai_router.py`）：
  - `POST /testcase/ai/generate/async` — 异步生成用例
  - `POST /testcase/ai/enhance/async` — 异步增强断言
  - `POST /testcase/ai/batch-generate/async` — 异步批量生成
- **Celery 配置**：任务序列化 JSON，结果过期 1 小时，软/硬时间限制 4/5 分钟

### AI 测试用例生成（Phase 4-5）

- **AI 服务**：`app/core/ai/openai_service.py` 封装 OpenAI/MiniMax API 调用
- **Prompt 模板**：`app/core/ai/prompt_template.py` 管理各类 Prompt
- **LangGraph 工作流**（Phase 5）：`app/core/ai/graph/` 实现 RAG → 生成 → 审查流程
  - `StateGraph` + `TypedDict` 定义状态
  - `retrieval` 节点：RAG 知识库检索
  - `generate` 节点：AI 生成测试用例
  - `review` 节点：AI 自我审查用例
- **API 端点**：
  - `POST /testcase/ai/generate` — 自然语言描述生成用例
  - `POST /testcase/ai/generate/graph` — LangGraph 工作流生成（Phase 5）
  - `POST /testcase/ai/enhance` — AI 增强断言
  - `POST /testcase/ai/batch-generate` — OpenAPI 批量生成
  - `POST /testcase/ai/parse-curl` — cURL 解析生成
  - `GET /testcase/ai/models` — 获取可用模型
- **配置项**（`config.py`）：`AI_OPENAI_API_KEY`、`AI_OPENAI_BASE_URL`、`AI_MODEL`、`AI_MAX_TOKENS`、`AI_TEMPERATURE`
- **错误处理**：AI 服务返回详细错误提示
  - 401/403 → "AI API 认证失败，请检查 AI_OPENAI_API_KEY 是否正确"
  - 404 → "AI API 地址错误，请检查 AI_OPENAI_BASE_URL 配置是否正确"
  - 422 → "AI 模型不存在或参数错误，请检查 AI_MODEL 配置是否正确"
  - 429 → "AI API 请求过于频繁，请稍后重试"
  - 500+ → "AI 服务端错误，请稍后重试"
  - 连接失败 → "AI API 连接失败，请检查 AI_OPENAI_BASE_URL 配置是否正确"
  - 超时 → "AI API 请求超时，请检查网络连接或稍后重试"
- **支持的 AI 服务商**：MiniMax、DeepSeek、智谱（GLM）

### 测试套件系统（Phase 3）

- **套件管理**：`TestSuite` 模型管理测试套件（名称、描述、所属项目、执行环境）
- **用例关联**：`TestSuiteCase` 关联套件与用例，支持顺序/并行执行模式
- **变量管理**：`TestSuiteVariable` 支持 string/json/yaml 类型的套件级变量
- **执行记录**：`TestSuiteExecution` 记录每次执行的开始/结束时间、通过/失败/错误数量
- **执行器**：`app/utils/suite_executor.py` 封装套件执行逻辑，支持失败重试、失败停止、并行执行

### 测试用例执行引擎

`app/core/executor.py` 是核心执行器，支持 5 种构造器类型：
- **HTTP** — `HttpConstructor`：发送 HTTP 请求
- **SQL** — `SqlConstructor`：执行数据库查询
- **Redis** — `RedisConstructor`：执行 Redis 命令
- **Python 脚本** — `PythonConstructor`：执行自定义 Python
- **测试用例** — `TestcaseConstructor`：嵌套调用其他用例

参数提取通过 `app/core/paramters/` 下的解析器（JSONPath、正则、状态码、KV）实现，全局配置解析通过 `app/utils/gconfig_parser.py`（String/JSON/YAML）。

### 配置（`config.py`）

`BaseConfig` 继承 `pydantic_settings.BaseSettings`（独立包），从 `.env` 文件加载。类常量需使用 `ClassVar` 注解。关键配置：
- MySQL/Redis 连接信息
- `REDIS_ON`：关闭 Redis 后定时任务可能重复执行
- `MOCK_ON` / `PROXY_ON`：Mock 服务器和代理开关
- `SERVER_REPORT`：测试报告 URL

## 新增 API 标准流程

1. **Model** — `app/models/` 创建模型类，直接继承 `Base` 并设置 `__tablename__`
2. **DAO** — `app/crud/` 下对应子目录创建 DAO 类，用 `@ModelWrapper(YourModel)` 装饰，继承 `Mapper`
3. **Schema** — `app/schema/` 创建 Pydantic v2 验证模型
4. **Router** — `app/routers/` 创建路由，用 `APIRouter` 定义端点
5. **Register** — 在 `main.py` 中 `pity.include_router()` 注册

## 架构原则：DAO vs Service

**沿袭 Pity 现有模式**：路由 → DAO → Model，不引入独立的 Service 层。

当以下任一条件满足时，考虑从 DAO 抽取到 Service：
1. **代码复制**：同一段业务逻辑出现在 2+ 个地方
2. **职责膨胀**：单个 DAO 超过 800 行且包含 3+ 个不同领域
3. **跨层复用**：需要在 HTTP、WebSocket、定时任务三种场景复用

拆分原则：从痛点出发，渐进式演进，保持接口兼容。

## 响应格式

```json
{"code": 0, "data": {}, "msg": "操作成功"}
```

| code | 含义 |
|------|------|
| 0 | 成功 |
| 101 | 参数错误（RequestValidationError 自动处理） |
| 110 | 业务异常 |
| 401 | 未登录（AuthException） |
| 403 | 无权限（PermissionException） |

## 日志

使用 Loguru，通过 `logger.bind(name=Config.PITY_INFO)` / `Config.PITY_ERROR` 分流：
- `logs/pity_info.log` — DEBUG 及以上
- `logs/pity_error.log` — WARNING 及以上

## 数据库迁移

项目配置了 Alembic（`alembic.ini` + `alembic/`），但启动时也会通过 `Base.metadata.create_all` 自动建表。Model 的 `__fields__`、`__tag__`、`__alias__`、`__show__` 类属性控制操作日志的展示字段和关联关系。

## 关键约定

- 不要修改 2025-10-12 之前编写的代码，优先创建新文件
- DAO 文件命名 `XxxDao.py`，放在 `app/crud/` 对应子目录下
- 前端 `localStorage` 中 JWT token 的 key 为 `pityToken`
- 所有 HTTP 响应 code 都在 200，业务错误通过 body 的 `code` 字段区分
- `app/crud/__init__.py` 启动时通过 `importlib` 动态导入所有 DAO 模块
- 模型继承：抽象类用 `PityBase`，需要建表的模型直接继承 `Base`
- 启动方式：`python pity.py`（生产）或 `uvicorn main:pity --reload`（开发）

## Phase 开发流程

每个 Phase 开发遵循以下流程：

### 开始 Phase
1. 在 `/Users/zhanzhicai/Desktop/Obsidian_one/AI学习笔记/pity/backend` 创建 Phase 计划文档
2. 文档命名格式：`PhaseX_功能名称实施记录.md`

### 开发过程中
- 发现问题或遗漏功能时，**立即追加**到 Obsidian 计划文档的"后续工作"列表
- 例如：发现"AI 生成用例没有保存到数据库"，立即添加 `- [ ] AI 生成用例保存到数据库`
- 解决一个问题后，更新为 `- [x] AI 生成用例保存到数据库（commit号）`
- 每次开发完成需要测试
  - 语法检查：`python3 -m py_compile <file>.py`
  - 启动后端验证服务正常：`python pity.py`
  - 核心功能手动测试

### 结束 Phase
1. **扫描遗漏内容**：
   - 检查本次 Phase 是否有发现但未记录的问题/功能
   - 检查"后续工作"列表中的待办是否都已完成
   - 确认所有功能点都已测试
2. 更新 Obsidian 计划文档：
   - 标记完成状态
   - 记录所有 commit
   - 列出新增/修改文件
   - 添加测试结果
   - 记录遇到的问题和解决方案
   - 更新后续工作清单
3. 在 `backend/CLAUDE.md` 更新开发阶段状态
4. 在 `backend/CLAUDE.md` 关键约定中添加本次 Phase 的关键架构说明
5. 提交代码：`git add -A && git commit -m "feat: Phase X 功能名称"`
   - 注意：推送由用户手动执行（网络问题导致推送失败的情况较多）

### Obsidian 文档标准结构
```markdown
# Phase X：功能名称实施记录

> 日期：YYYY-MM-DD
> 状态：进行中/已完成
> 分支：feat/upgrade-plugin-system
> 最新 Commit：xxxxxx

## 更新记录

| 日期 | Commit | 更新内容 |
|------|--------|----------|
| YYYY-MM-DD | xxxxxx | 描述 |

## 完成情况
- [x] 功能点1
- [ ] 功能点2

## API 端点
（表格列出所有接口）

## 测试结果
（命令和响应）

## 测试检查清单：核心功能手动测试
(表格列出所有接口）

## 修复的问题
1. 问题描述 - 解决方案

## 后续工作
- [ ] 待办1
- [ ] 待办2
```

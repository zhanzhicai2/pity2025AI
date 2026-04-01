# AI如何辅助全栈开发指南

> **项目结构**
> - **后端**: `/Users/zhanzhicai/Desktop/py/pity` (PyCharm + FastAPI)
> - **前端**: `/Users/zhanzhicai/Desktop/py/pityweb2025Ai` (WebStorm + React 18 + TypeScript)
> - **部署**: 前端build后的文件在 `pity/statics/` 目录

---

## 📋 目录
1. [高效开发工作流](#高效开发工作流)
2. [AI辅助技巧](#ai辅助技巧)
3. [对话模板](#对话模板)
4. [实战案例](#实战案例)

---

## 🚀 高效开发工作流

### 日常开发模式

```
┌─────────────────────────────────────────────────────────┐
│                    开发模式                               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  前端开发服务器              后端API服务器                │
│  localhost:8000             localhost:7777               │
│  (WebStorm)                 (PyCharm)                    │
│       │                          │                       │
│       │     API请求              │                       │
│       ├─────────────────────────►│                       │
│       │                          │                       │
│       │     返回数据              │                       │
│       │◄─────────────────────────┤                       │
│                                                           │
└─────────────────────────────────────────────────────────┘

开发命令:
- 前端: cd pityweb2025Ai && npm run start:dev
- 后端: cd pity && python main.py
```

### 生产部署模式

```
┌─────────────────────────────────────────────────────────┐
│                    生产模式                               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│              FastAPI服务器 0.0.0.0:7777                  │
│                                                           │
│  ├── 动态API接口  (app/routers/)                         │
│  │                                                         │
│  └── 静态文件服务  (statics/)                             │
│      ↑                                                    │
│      │                                                    │
│      └── 前端build产物                                     │
│          (npm run build → dist/* → statics/)             │
│                                                           │
└─────────────────────────────────────────────────────────┘

部署命令:
1. cd pityweb2025Ai && npm run build
2. cp -r dist/* ../pity/statics/
3. cd pity && python main.py
4. 访问: http://localhost:7777
```

---

## 🎯 AI辅助技巧

### 技巧1: 为AI提供项目上下文

**每次对话开始时声明：**

```markdown
【项目说明】
项目名称: Pity API测试平台
技术栈:
- 后端: FastAPI + SQLAlchemy + MySQL + Redis (PyCharm开发)
- 前端: React 18 + TypeScript + UmiJS + Ant Design (WebStorm开发)
- 部署: 前端build后放在后端statics目录

目录结构:
- 后端: /Users/zhanzhicai/Desktop/py/pity
- 前端: /Users/zhanzhicai/Desktop/py/pityweb2025Ai
```

### 技巧2: 标注前后端关联

**在代码中添加AI提示注释：**

```python
# 后端代码 (app/routers/testcase.py)
@app.post("/testcase", summary="创建测试用例")
async def create_testcase(
    testcase: TestCaseCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    创建测试用例

    AI辅助信息:
    - 前端调用: src/services/testcase.js -> createTestCase()
    - 前端页面: src/pages/TestCase/index.tsx
    - 数据流: 表单 → API → DAO → MySQL
    - 权限要求: 需要登录

    前端开发注意事项:
    - 请求头需要添加 Authorization: Bearer {token}
    - 响应格式: { code: 0, data: TestCase, msg: "success" }
    """
```

```typescript
// 前端代码 (src/services/testcase.js)
/**
 * 创建测试用例
 *
 * AI辅助信息:
 * - 后端接口: POST /api/testcase
 * - 后端文件: app/routers/testcase.py:45
 * - 数据模型: TestCase (app/models/testcase.py)
 *
 * 后端开发注意事项:
 * - 需要 AsyncSession 依赖注入
 * - 返回 TestCaseResponse 类型
 * - 异常处理: 使用 try-except
 */
export async function createTestCase(data: any) {
  return request('/api/testcase', {
    method: 'POST',
    data,
  });
}
```

### 技巧3: 创建API映射文档

**创建 `API映射.md`：**

```markdown
# 前后端API映射

## 用户认证
| 功能 | 前端服务 | 后端路由 | 数据模型 |
|------|---------|---------|---------|
| 登录 | src/services/auth.ts:login() | POST /api/auth/login | User |
| 注册 | src/services/auth.ts:register() | POST /api/auth/register | User |
| 登出 | src/services/auth.ts:logout() | POST /api/auth/logout | - |

## 测试用例
| 功能 | 前端服务 | 后端路由 | 数据模型 |
|------|---------|---------|---------|
| 创建 | src/services/testcase.js:createTestCase() | POST /api/testcase | TestCase |
| 查询 | src/services/testcase.js:getTestCaseList() | GET /api/testcase/list | TestCase |
| 更新 | src/services/testcase.js:updateTestCase() | PUT /api/testcase | TestCase |
| 删除 | src/services/testcase.js:deleteTestCase() | DELETE /api/testcase | TestCase |
```

---

## 💬 对话模板

### 模板1: 添加新功能

```markdown
【开发任务】添加测试用例批量删除功能

【项目信息】
- 后端: FastAPI (PyCharm)
- 前端: React + TypeScript (WebStorm)
- 后端目录: /Users/zhanzhicai/Desktop/py/pity
- 前端目录: /Users/zhanzhicai/Desktop/py/pityweb2025Ai

【需求】
1. 后端添加批量删除接口
   - 路由: DELETE /api/testcase/batch
   - 参数: { case_ids: number[] }
   - 返回: { deleted_count: number }

2. 前端添加批量操作
   - 列表页添加批量选择
   - 添加批量删除按钮
   - 显示删除成功数量

【现有文件】
- 后端路由: app/routers/testcase.py
- 前端服务: src/services/testcase.js
- 前端页面: src/pages/TestCase/index.tsx

【要求】
- 完整的类型注解
- 错误处理
- 权限验证
- 中文注释

请生成完整代码并说明修改位置。
```

### 模板2: 调试API问题

```markdown
【问题】前端调用后端API失败

【项目】
- 前端: http://localhost:8000 (React + WebStorm)
- 后端: http://localhost:7777 (FastAPI + PyCharm)

【错误信息】
前端Console:
```
TypeError: Cannot read property 'data' of undefined
  at TestCaseComponent.tsx:45
```

Network Request:
```
URL: POST /api/testcase
Status: 400 Bad Request
Request: { "name": "测试用例", "project_id": 1 }
Response: { "code": 101, "msg": "缺少参数: case_name" }
```

【相关代码】
前端 (src/pages/TestCase/index.tsx):
```typescript
const handleSubmit = async (values: any) => {
  const response = await createTestCase({
    name: values.name,
    project_id: values.projectId,
  });
  console.log(response);
};
```

后端 (app/routers/testcase.py):
```python
@app.post("/testcase")
async def create_testcase(
    testcase: TestCaseCreate,
    session: AsyncSession = Depends(get_session)
):
    return await TestCaseDao.create(session, testcase)
```

Schema (app/schema/testcase.py):
```python
class TestCaseCreate(BaseModel):
    case_name: str  # 注意：这里是 case_name
    project_id: int
```

【我的分析】
看起来前端发送的是 `name`，但后端期望的是 `case_name`

请帮我：
1. 确认问题原因
2. 提供修复方案（应该改前端还是后端？）
3. 给出修改后的代码
```

### 模板3: 代码审查

```markdown
【代码审查请求】

【代码说明】
功能: 测试用例列表查询
文件: app/routers/testcase.py
最近修改: 添加了缓存功能

【代码】
```python
@app.get("/testcase/list")
async def list_testcases(
    page: int = 1,
    size: int = 10,
    session: AsyncSession = Depends(get_session)
):
    # 从Redis获取缓存
    cache_key = f"testcase_list_{page}_{size}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 查询数据库
    result = await TestCaseDao.list(session, page, size)

    # 设置缓存
    await redis.setex(cache_key, 300, json.dumps(result))

    return result
```

【审查要点】
请关注：
1. 缓存策略是否合理
2. 性能优化空间
3. 潜在的bug
4. 代码规范
5. 错误处理

技术栈: FastAPI + Redis + SQLAlchemy
```

### 模板4: 理解现有代码

```markdown
【代码理解请求】

【文件】
后端: app/routers/testcase.py
前端: src/services/testcase.js

【代码】
[粘贴代码]

【问题】
1. 这段代码的整体流程是什么？
2. 前后端是如何交互的？
3. 数据格式是如何转换的？
4. 有哪些关键的依赖？
5. 如果要添加新功能，应该修改哪些地方？

【我的理解】
[说明你的理解，让AI纠正或补充]

请详细解释，并结合前后端代码说明。
```

---

## 🎓 实战案例

### 案例1: 开发用户组管理功能

**第1步: 让AI规划**

```markdown
我要开发一个用户组管理功能，包含列表、创建、编辑、删除。

项目信息:
- 后端: FastAPI + SQLAlchemy (PyCharm)
- 前端: React + Ant Design (WebStorm)

请帮我规划：
1. 需要创建哪些文件？
2. 前后端如何分工？
3. 开发顺序建议？
4. 需要注意的点？
```

**第2步: 让AI生成后端代码**

```markdown
根据规划，请帮我生成后端代码：

需求:
- 数据模型: UserGroup (id, name, description, created_at)
- DAO: app/crud/UserGroupDao.py
- 路由: app/routers/usergroup.py
- Schema: app/schema/usergroup.py

要求:
- 完整的CRUD操作
- 异步编程
- 类型注解
- 中文注释
- 错误处理
```

**第3步: 让AI生成前端代码**

```markdown
根据后端接口，生成前端代码：

后端接口:
- GET /api/usergroup/list - 列表
- POST /api/usergroup - 创建
- PUT /api/usergroup/{id} - 更新
- DELETE /api/usergroup/{id} - 删除

需求:
1. API服务: src/services/usergroup.ts
2. 页面组件: src/pages/UserGroup/index.tsx
3. 使用Ant Design ProTable
4. 包含搜索、分页、批量删除

要求:
- TypeScript类型定义
- 错误处理
- Loading状态
- 权限控制
```

**第4步: 让AI审查代码**

```markdown
帮我审查刚才生成的代码：

[粘贴代码]

关注点:
1. 前后端类型是否一致？
2. 错误处理是否完善？
3. 是否有性能问题？
4. 代码是否规范？
```

### 案例2: 调试前后端联调问题

```markdown
【联调问题】

现象:
前端点击"保存测试用例"按钮后，显示保存成功，但刷新页面后数据丢失。

环境:
- 前端: http://localhost:8000 (WebStorm)
- 后端: http://localhost:7777 (PyCharm)

前端代码 (src/pages/TestCase/EditModal.tsx):
```typescript
const handleSave = async () => {
  try {
    const values = await form.validateFields();
    await updateTestCase(caseId, values);
    message.success('保存成功');
    setVisible(false);
  } catch (error) {
    message.error('保存失败');
  }
};
```

后端代码 (app/routers/testcase.py):
```python
@app.put("/testcase")
async def update_testcase(
    case_id: int,
    testcase: TestCaseUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await TestCaseDao.update(session, case_id, testcase)
    await session.commit()  # 注意：这里commit了
    return result
```

日志:
```
[2025-01-06 10:30:00] INFO - 更新测试用例: id=123
[2025-01-06 10:30:00] INFO - 事务未提交，等待外层commit
```

我的分析:
看起来commit被执行了，但数据没有真正保存。可能是因为FastAPI的依赖注入自动管理事务？

请帮我：
1. 确认问题原因
2. 说明FastAPI的事务管理机制
3. 提供正确的代码
```

### 案例3: 性能优化

```markdown
【性能优化请求】

问题:
测试用例列表页面加载很慢，首屏需要5秒

环境:
- 数据量: 10000条测试用例
- 前端: React + ProTable
- 后端: FastAPI + MySQL

前端代码 (src/pages/TestCase/index.tsx):
```typescript
<ProTable
  request={async (params) => {
    const result = await getTestCaseList({
      page: params.current,
      size: params.pageSize,
    });
    return {
      data: result.data,
      success: true,
      total: result.total,
    };
  }}
  columns={columns}
/>
```

后端代码 (app/routers/testcase.py):
```python
@app.get("/testcase/list")
async def list_testcases(
    page: int = 1,
    size: int = 10,
    session: AsyncSession = Depends(get_session)
):
    # 查询总数
    total = await session.execute(
        select(func.count(TestCase.id))
    )

    # 查询列表
    result = await session.execute(
        select(TestCase)
        .offset((page - 1) * size)
        .limit(size)
    )

    # 查询每个用例的关联数据
    data = []
    for case in result.scalars():
        case.project = await session.get(Project, case.project_id)
        case.user = await session.get(User, case.create_user)
        data.append(case)

    return {"data": data, "total": total}
```

分析:
1. N+1查询问题：每个case都要查询project和user
2. 没有使用索引
3. 没有缓存

请提供：
1. SQL优化方案（使用join）
2. 添加合适的索引
3. Redis缓存方案
4. 前端虚拟滚动方案
```

---

## 🛠️ 实用技巧

### 技巧1: 利用IDE的TODO功能

```python
# PyCharm中
# TODO: [AI辅助] 需要添加参数验证
# FIXME: [AI协助] 这里性能有问题，需要优化
# HACK: 临时方案，等待AI重构
```

```typescript
// WebStorm中
// TODO: [AI辅助] 添加错误处理
// FIXME: [AI协助] 组件太大了，需要拆分
```

### 技巧2: 使用Git进行AI辅助

```bash
# 开发前
git checkout -b feature/new-function

# 开发中，让AI检查改动
git diff
# 复制diff内容，让AI review

# 开发完成后，让AI生成commit message
git add .
# 让AI: "根据这些改动生成规范的commit message"
```

### 技巧3: 分阶段对话

```markdown
# 第1阶段：理解需求
"我要实现一个xxx功能，帮我分析一下需要做什么"

# 第2阶段：设计方案
"根据分析，帮我设计技术方案"

# 第3阶段：生成代码
"根据方案，生成代码框架"

# 第4阶段：完善代码
[自己填充业务逻辑]

# 第5阶段：代码审查
"帮我review这段代码"
```

---

## 📝 快速参考

### 常用对话场景

| 场景 | 提示词 |
|------|--------|
| 新功能 | "我要实现xxx功能，项目是FastAPI+React，请帮我规划并生成代码" |
| Bug修复 | "遇到错误：[粘贴错误]，相关代码：[粘贴代码]，请帮我分析原因" |
| 代码优化 | "这段代码性能不好：[粘贴代码]，请帮我优化" |
| 代码理解 | "请解释这段代码：[粘贴代码]" |
| 代码审查 | "请review这段代码，关注性能和安全：[粘贴代码]" |
| 技术学习 | "请结合我的项目讲解xxx技术" |

### 项目信息速查

```markdown
后端:
- 目录: /Users/zhanzhicai/Desktop/py/pity
- 启动: python main.py
- 端口: 7777
- 文档: http://localhost:7777/docs
- 日志: logs/pity_error.log

前端:
- 目录: /Users/zhanzhicai/Desktop/py/pityweb2025Ai
- 启动: npm run start:dev
- 端口: 8000
- 构建: npm run build
- 部署: cp -r dist/* ../pity/statics/
```

---

## 💡 最佳实践

### 1. 保持对话上下文

```markdown
# 好的做法
每次对话开始时：
"继续之前的FastAPI+React项目，现在我要..."

# 不好的做法
直接开始新话题，不提供上下文
```

### 2. 提供完整信息

```markdown
# 包含的信息:
- 技术栈 (FastAPI + React)
- 开发工具 (PyCharm + WebStorm)
- 文件路径 (完整路径)
- 错误信息 (完整堆栈)
- 相关代码 (包含导入语句)
- 环境信息 (版本号)
```

### 3. 循序渐进

```markdown
# 好的做法
1. 先让AI理解需求
2. 再让AI设计方案
3. 然后生成代码框架
4. 自己填充业务逻辑
5. 最后让AI review

# 不好的做法
一次性要求AI完成所有工作
```

### 4. 标注前后端关联

```markdown
# 在代码注释中标注:
# 后端: "前端调用: src/services/testcase.js:45"
# 前端: "后端接口: app/routers/testcase.py:123"
```

---

## 🎯 总结

**让AI更好辅助你的关键点：**

1. ✅ 提供完整的项目上下文
2. ✅ 标注前后端关联关系
3. ✅ 使用结构化的对话模板
4. ✅ 分阶段进行复杂任务
5. ✅ 保持代码注释的详细性
6. ✅ 利用IDE的工具（TODO、书签）
7. ✅ 定期让AI review 代码
8. ✅ 建立API映射文档

**记住：**
- AI是你的助手，不是替代者
- 你需要理解代码，而不是盲目复制
- 多与AI交流，它会越来越了解你的项目
- 保持学习的态度，结合AI的建议提升自己

---

**祝开发顺利！** 🚀
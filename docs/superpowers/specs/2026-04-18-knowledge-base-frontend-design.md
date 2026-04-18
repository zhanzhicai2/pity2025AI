# 知识库前端页面设计文档

> 日期：2026-04-18
> 状态：已批准
> 分支：feat/upgrade-plugin-system
> 前端仓库：pityweb2025AI

## 概述

为已有的后端 RAG 知识库系统实现前端页面。后端已实现文档上传、解析、向量化、检索等功能，前端需要新增知识库管理界面。

## 数据模型

```
项目(Project) 1:N 知识库(KnowledgeBase) 1:N 文档(Knowledge/Document)
```

## 页面路由

- 路径：`/ai/knowledge`
- 菜单位置：AI管理 子菜单，与"AI对话"、"LLM配置"、"用例生成"并列
- 页面组件：`src/pages/AI/KnowledgeBase/KnowledgeBase.jsx`
- `project_id` 来源：通过 `useProject` hook 获取当前项目 ID（与项目其他页面一致）
- 前端 proxy：需在 `config/proxy.ts` 添加 `/rag/` 代理到后端 `localhost:7777`

## 技术选型

| 项目 | 选择 | 理由 |
|------|------|------|
| 状态管理 | hooks + useState | `useModel` 依赖 dva 初始化时序，可能返回 undefined |
| API 调用 | umi-request | 与项目现有 service 文件一致 |
| 布局组件 | react-split-pane | 与 TestCaseDirectory 页面一致 |
| UI 组件库 | Ant Design v5 | 项目标准 |
| 日期处理 | moment | 项目标准 |
| 文件格式 | JavaScript (.js/.jsx) | 新文件必须使用 JS |

## 文件结构

```
src/pages/AI/KnowledgeBase/
├── KnowledgeBase.jsx              # 主布局（SplitPane 编排）
├── components/
│   ├── KnowledgeBaseList.jsx      # 左侧：知识库列表（hover 显示编辑/删除）
│   ├── DocumentTable.jsx          # 右侧：文档表格 + 操作栏
│   ├── KnowledgeBaseForm.jsx      # 新建/编辑知识库弹窗（Modal）
│   ├── DocumentUpload.jsx         # 上传文档弹窗（Modal + Dragger）
│   └── DocumentDetail.jsx         # 文档详情抽屉（Drawer）
├── hooks/
│   ├── useKnowledgeBase.js        # 知识库 CRUD + 列表状态
│   └── useDocuments.js            # 文档管理 + 搜索状态
└── services.js                    # API 调用（umi-request + auth.headers）
```

## 页面布局

### 整体结构

```
PageContainer
└── Card
    └── SplitPane (defaultSize: 280px, minSize: 200px)
        ├── ScrollCard (左侧 - 知识库导航)
        └── ScrollCard (右侧 - 文档管理)
```

### 左侧面板 — KnowledgeBaseList

```
ScrollCard
├── Input.Search (placeholder="搜索知识库")
├── Button (+ 新建, type="primary", block)
└── List
    └── ListItem (每个知识库)
        ├── 左侧：知识库名称 + 文档数 badge
        └── 右侧：Dropdown (hover 触发)
            └── Menu
                ├── 编辑 (打开 KnowledgeBaseForm)
                └── 删除 (Popconfirm 确认)
```

交互：
- 点击列表项 → 选中高亮，右侧加载该知识库文档
- hover 列表项 → 右侧显示操作图标，展开编辑/删除菜单
- 搜索框 → 实时过滤知识库名称
- 选中态：`background: #e6f7ff`, `border-left: 3px solid #1677ff`

### 右侧面板 — DocumentTable

```
ScrollCard
├── 知识库信息栏
│   ├── 知识库名称 (h3)
│   ├── 描述文本 (color: #999)
│   └── 统计标签 (Tag)
│       ├── 文档数 (default)
│       ├── 已处理 (green)
│       └── 失败 (red)
│
├── 操作栏
│   ├── 左侧
│   │   ├── Input.Search (搜索文档关键词)
│   │   └── Checkbox ("搜索全部知识库")
│   └── 右侧
│       ├── Button (上传文档, icon="upload")
│       ├── Button (刷新文档, icon="reload")
│       ├── Button (查询, type="primary")
│       └── Button (重置)
│
└── Table (bordered)
    ├── 标题 (dataIndex="name")
    ├── 类型 (Tag: PDF=blue, DOCX=purple, MD=orange, TXT=default)
    ├── 大小 (格式化: KB/MB)
    ├── 分块数 (dataIndex="chunk_count")
    ├── 状态 (Badge: pending=orange, processing=blue, ready=green, error=red)
    ├── 上传时间 (moment 格式化 YYYY-MM-DD HH:mm)
    └── 操作 (查看 → DocumentDetail / 删除 → Popconfirm)
```

未选中知识库时：显示 `Empty` 组件，提示"请选择左侧知识库查看文档"。

### 搜索范围切换

- **未勾选"搜索全部知识库"**：`GET /rag/search?kb_id={currentId}&keyword=xxx`
- **勾选"搜索全部知识库"**：`GET /rag/search?project_id={projectId}&keyword=xxx`

## 弹窗组件

### KnowledgeBaseForm（新建/编辑）

```
Modal (width=520px)
├── Form (labelCol=6, wrapperCol=16)
│   ├── 名称 (Input, required, max=50)
│   ├── 描述 (TextArea, rows=3, max=200)
│   ├── 分块大小 (InputNumber, default=500, min=100, max=2000)
│   └── 重叠大小 (InputNumber, default=50, min=0, max=500)
└── Footer: 取消 / 保存(type="primary", loading)
```

### DocumentUpload（上传文档）

```
Modal (width=600px)
├── Upload.Dragger
│   ├── 提示: "点击或拖拽文件到此区域上传"
│   ├── 支持格式: .pdf, .docx, .md, .txt
│   └── multiple=true, 上传前校验文件类型
├── 已上传文件列表 (Upload fileList)
└── Footer: 关闭 (上传完成后自动刷新文档列表)
```

上传接口：`POST /rag/upload`，`multipart/form-data`，含 `kb_id` 参数。

### DocumentDetail（文档详情）

```
Drawer (width=640px, placement="right")
├── Descriptions (column=2)
│   ├── 文档名称 / 文件类型 (Tag) / 文件大小
│   ├── 分块数量 / 状态 (Badge) / 上传时间
│   └── 错误信息 (仅 status=error 时, Alert)
└── 分块预览
    └── Collapse
        └── Panel (每个分块, header="分块 #1, #2, ...")
            └── 分块文本内容 (Typography.Paragraph, ellipsis)
```

## API 映射

| 前端函数 | Method | 后端端点 | 状态 |
|---------|--------|---------|------|
| `getKnowledgeBases(projectId)` | GET | `/rag/knowledge-bases?project_id={id}` | 缺失 |
| `createKnowledgeBase(data)` | POST | `/rag/knowledge-bases` | 缺失 |
| `updateKnowledgeBase(id, data)` | PUT | `/rag/knowledge-bases/{id}` | 缺失 |
| `deleteKnowledgeBase(id)` | DELETE | `/rag/knowledge-bases/{id}` | 缺失 |
| `getDocuments(kbId)` | GET | `/rag/list?kb_id={id}` | 需修改 |
| `uploadDocument(kbId, file)` | POST | `/rag/upload` | 需修改 |
| `deleteDocument(docId)` | DELETE | `/rag/{doc_id}` | 已有 |
| `getDocumentDetail(docId)` | GET | `/rag/{doc_id}` | 已有 |
| `searchDocuments(kbId, keyword)` | GET | `/rag/search?kb_id={id}&keyword=xxx` | 需修改 |
| `searchAllDocuments(projectId, keyword)` | GET | `/rag/search?project_id={id}&keyword=xxx` | 需新增 |

## 后端缺失分析

### 缺失 1：知识库模型层

新增 `KnowledgeBase` 模型：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 主键 |
| name | str | 知识库名称 |
| description | str | 描述 |
| chunk_size | int | 分块大小, default=500 |
| overlap | int | 重叠大小, default=50 |
| project_id | int, FK | 关联项目 |
| document_count | int | 文档统计 |
| create_user | int, FK | 创建者 |
| created_at / updated_at | datetime | 时间戳 |

修改 `Knowledge` 模型：新增 `kb_id` (int, FK → knowledge_base)。

### 缺失 2：知识库 DAO 层

新增 `app/crud/knowledge_base/KnowledgeBaseDao.py`：
- `create_knowledge_base` / `update_knowledge_base` / `delete_knowledge_base`
- `list_knowledge_bases(project_id)` / `get_knowledge_base(kb_id)`

### 缺失 3：知识库 Router 层

新增 `app/routers/rag/kb_router.py`：
- `POST /rag/knowledge-bases` / `GET /rag/knowledge-bases`
- `PUT /rag/knowledge-bases/{id}` / `DELETE /rag/knowledge-bases/{id}`

### 缺失 4：现有接口修改

| 接口 | 修改 |
|------|------|
| `POST /rag/upload` | 新增 `kb_id` 参数 |
| `GET /rag/list` | 新增 `kb_id` 筛选 |
| `GET /rag/search` | 支持按 `kb_id` 或 `project_id` 搜索 |

### 缺失 5：ChromaDB 集合管理

- 每个知识库一个 collection（命名：`kb_{id}`）
- 搜索时指定 collection（单 KB）或跨 collection（全局）

## 后端开发优先级

```
P0 (前端阻塞):
  1. KnowledgeBase 模型 + 迁移
  2. KnowledgeBase DAO（CRUD）
  3. KnowledgeBase Router（4 个端点）
  4. 修改 upload/list/search 支持 kb_id

P1 (功能完善):
  5. ChromaDB 按知识库分 collection
  6. 全局搜索（跨 KB）
  7. 删除知识库时级联清理文档 + 向量

P2 (体验优化):
  8. 知识库文档统计（document_count 缓存更新）
  9. 文档处理状态 WebSocket 推送
```

## Hooks 设计

### useKnowledgeBase

```js
状态: list, currentId, loading, formVisible, editingKB
方法: fetchList, selectKB, create, update, remove
```

### useDocuments

```js
状态: documents, loading, searchKeyword, searchAll, detailVisible, detailData
方法: fetchList, upload, remove, search, setDetail
依赖: currentId (from useKnowledgeBase)
```

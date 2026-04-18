# 知识库前端页面实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为已有后端 RAG 系统实现前端知识库管理页面，包含知识库 CRUD、文档管理、关键词检索功能。

**Architecture:** 后端新增 `KnowledgeLib` 容器模型 + DAO + Router，修改现有文档接口支持 `lib_id`。前端使用 SplitPane 布局 + hooks 状态管理 + 模块化组件。

**Tech Stack:** FastAPI + SQLAlchemy 2.0 + Pydantic v2（后端）| UmiJS 4 + Ant Design v5 + react-split-pane + umi-request（前端）

**Spec:** `docs/superpowers/specs/2026-04-18-knowledge-base-frontend-design.md`

**仓库说明：**
- 后端：`/Users/zhanzhicai/Desktop/py/pity/backend`（当前仓库）
- 前端：`/Users/zhanzhicai/Desktop/py/pity/pityweb2025AI`（独立仓库）
- 提交：各自独立提交到本地，不推送

---

## Task 1: 后端 — 创建 KnowledgeLib 容器模型

**Files:**
- Create: `app/models/knowledge_lib.py`

- [ ] **Step 1: 创建 KnowledgeLib 模型文件**

```python
# app/models/knowledge_lib.py
"""知识库容器模型"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models import Base


class KnowledgeLib(Base):
    """知识库（容器）"""
    __tablename__ = "knowledge_lib"
    __table_args__ = {'comment': '知识库容器表', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="知识库描述")
    chunk_size = Column(Integer, default=500, comment="分块大小")
    overlap = Column(Integer, default=50, comment="重叠大小")
    project_id = Column(Integer, nullable=False, comment="所属项目ID")
    document_count = Column(Integer, default=0, comment="文档数量")
    create_user = Column(Integer, nullable=True, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
```

- [ ] **Step 2: 验证语法**

Run: `cd /Users/zhanzhicai/Desktop/py/pity/backend && python3 -m py_compile app/models/knowledge_lib.py`
Expected: 无输出（编译成功）

- [ ] **Step 3: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && git add app/models/knowledge_lib.py && git commit -m "feat: 新增 KnowledgeLib 知识库容器模型"
```

---

## Task 2: 后端 — 修改 KnowledgeBase 文档模型，添加 lib_id

**Files:**
- Modify: `app/models/knowledge_base.py`

- [ ] **Step 1: 在 KnowledgeBase 模型中添加 lib_id 字段**

在 `app/models/knowledge_base.py` 的 `KnowledgeBase` 类中，`name` 字段之前添加：

```python
    lib_id = Column(Integer, nullable=True, comment="所属知识库ID")
```

- [ ] **Step 2: 验证语法**

Run: `cd /Users/zhanzhicai/Desktop/py/pity/backend && python3 -m py_compile app/models/knowledge_base.py`

- [ ] **Step 3: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && git add app/models/knowledge_base.py && git commit -m "feat: KnowledgeBase 文档模型添加 lib_id 外键"
```

---

## Task 3: 后端 — 创建 KnowledgeLib Schema + DAO

**Files:**
- Create: `app/schema/knowledge_lib_schema.py`
- Create: `app/crud/knowledge_lib/__init__.py`
- Create: `app/crud/knowledge_lib/KnowledgeLibDao.py`

- [ ] **Step 1: 创建 Schema**

```python
# app/schema/knowledge_lib_schema.py
"""KnowledgeLib Pydantic v2 Schema"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeLibCreate(BaseModel):
    name: str = Field(..., max_length=50, description="知识库名称")
    description: Optional[str] = Field(None, max_length=200, description="描述")
    chunk_size: int = Field(500, ge=100, le=2000, description="分块大小")
    overlap: int = Field(50, ge=0, le=500, description="重叠大小")
    project_id: int = Field(..., description="所属项目ID")


class KnowledgeLibUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    chunk_size: Optional[int] = Field(None, ge=100, le=2000)
    overlap: Optional[int] = Field(None, ge=0, le=500)


class KnowledgeLibResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    chunk_size: int = 500
    overlap: int = 50
    project_id: int
    document_count: int = 0
    create_user: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

- [ ] **Step 2: 创建 DAO 目录和 __init__.py**

```bash
mkdir -p /Users/zhanzhicai/Desktop/py/pity/backend/app/crud/knowledge_lib
```

创建空的 `__init__.py`。

- [ ] **Step 3: 创建 DAO**

```python
# app/crud/knowledge_lib/KnowledgeLibDao.py
"""KnowledgeLib DAO"""
from typing import List, Tuple

from app.crud import Mapper, ModelWrapper, connect
from app.models.knowledge_lib import KnowledgeLib


@ModelWrapper(KnowledgeLib)
class KnowledgeLibDao(Mapper):
    """知识库容器 DAO"""

    @classmethod
    @connect
    async def create_knowledge_lib(
        cls, name, project_id, description=None,
        chunk_size=500, overlap=50, user_id=None, session=None
    ):
        """创建知识库"""
        model = KnowledgeLib()
        model.name = name
        model.project_id = project_id
        model.description = description
        model.chunk_size = chunk_size
        model.overlap = overlap
        model.create_user = user_id
        model.document_count = 0
        return await cls.insert(model=model, session=session)

    @classmethod
    @connect
    async def update_knowledge_lib(
        cls, lib_id, name=None, description=None,
        chunk_size=None, overlap=None, session=None
    ):
        """更新知识库"""
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if chunk_size is not None:
            kwargs["chunk_size"] = chunk_size
        if overlap is not None:
            kwargs["overlap"] = overlap
        await cls.update_by_id(lib_id, session=session, **kwargs)

    @classmethod
    @connect
    async def list_knowledge_libs(
        cls, project_id=None, session=None
    ) -> Tuple[List, int]:
        """列出知识库"""
        kwargs = {}
        if project_id is not None:
            kwargs["project_id"] = project_id
        return await cls.list_with_pagination(1, 1000, session=session, **kwargs)

    @classmethod
    @connect
    async def get_knowledge_lib(cls, lib_id, session=None):
        """获取单个知识库"""
        from app.crud import Mapper as BaseMapper
        return await BaseMapper.query_record(cls, id=lib_id)

    @classmethod
    @connect
    async def delete_knowledge_lib(cls, lib_id, user_id=None, session=None):
        """删除知识库"""
        from app.crud import Mapper as BaseMapper
        await BaseMapper.delete_record_by_id(
            cls, session=session, user=user_id, value=lib_id
        )

    @classmethod
    @connect
    async def update_document_count(cls, lib_id, session=None):
        """更新文档数量统计"""
        from sqlalchemy import select, func
        from app.models.knowledge_base import KnowledgeBase
        stmt = select(func.count()).where(
            KnowledgeBase.lib_id == lib_id,
            KnowledgeBase.deleted_at == 0
        )
        result = await session.execute(stmt)
        count = result.scalar()
        await cls.update_by_id(lib_id, session=session, document_count=count)
```

- [ ] **Step 4: 验证语法**

Run:
```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && python3 -m py_compile app/schema/knowledge_lib_schema.py && python3 -m py_compile app/crud/knowledge_lib/KnowledgeLibDao.py
```

- [ ] **Step 5: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && git add app/schema/knowledge_lib_schema.py app/crud/knowledge_lib/ && git commit -m "feat: 新增 KnowledgeLib Schema 和 DAO"
```

---

## Task 4: 后端 — 创建 KnowledgeLib Router

**Files:**
- Create: `app/routers/rag/kb_router.py`
- Modify: `main.py`（注册路由）

- [ ] **Step 1: 创建知识库 CRUD 路由**

```python
# app/routers/rag/kb_router.py
"""知识库容器 CRUD 路由"""
from fastapi import APIRouter, Depends

from app.crud.knowledge_lib.KnowledgeLibDao import KnowledgeLibDao
from app.routers import Permission
from app.schema.knowledge_lib_schema import (
    KnowledgeLibCreate,
    KnowledgeLibUpdate,
    KnowledgeLibResponse,
)
from app.handler.fatcory import PityResponse

kb_router = APIRouter(prefix="/rag/knowledge-bases", tags=["KnowledgeBase CRUD"])


@kb_router.post("")
async def create_knowledge_base(
    body: KnowledgeLibCreate,
    user_info: dict = Depends(Permission()),
):
    """创建知识库"""
    user_id = user_info.get("id")
    try:
        record = await KnowledgeLibDao.create_knowledge_lib(
            name=body.name,
            project_id=body.project_id,
            description=body.description,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
            user_id=user_id,
        )
        return PityResponse.success(KnowledgeLibResponse.model_validate(record))
    except Exception as e:
        return PityResponse.failed(f"创建知识库失败: {e}")


@kb_router.get("")
async def list_knowledge_bases(
    project_id: int,
    user_info: dict = Depends(Permission()),
):
    """列出知识库"""
    try:
        data, total = await KnowledgeLibDao.list_knowledge_libs(project_id=project_id)
        return PityResponse.success(
            [KnowledgeLibResponse.model_validate(d) for d in data]
        )
    except Exception as e:
        return PityResponse.failed(f"查询失败: {e}")


@kb_router.get("/{lib_id}")
async def get_knowledge_base(
    lib_id: int,
    user_info: dict = Depends(Permission()),
):
    """获取知识库详情"""
    try:
        record = await KnowledgeLibDao.get_knowledge_lib(lib_id)
        if record is None:
            return PityResponse.failed("知识库不存在")
        return PityResponse.success(KnowledgeLibResponse.model_validate(record))
    except Exception as e:
        return PityResponse.failed(f"查询失败: {e}")


@kb_router.put("/{lib_id}")
async def update_knowledge_base(
    lib_id: int,
    body: KnowledgeLibUpdate,
    user_info: dict = Depends(Permission()),
):
    """更新知识库"""
    try:
        await KnowledgeLibDao.update_knowledge_lib(
            lib_id=lib_id,
            name=body.name,
            description=body.description,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
        )
        return PityResponse.success(msg="更新成功")
    except Exception as e:
        return PityResponse.failed(f"更新失败: {e}")


@kb_router.delete("/{lib_id}")
async def delete_knowledge_base(
    lib_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除知识库"""
    user_id = user_info.get("id")
    try:
        await KnowledgeLibDao.delete_knowledge_lib(lib_id=lib_id, user_id=user_id)
        return PityResponse.success(msg="删除成功")
    except Exception as e:
        return PityResponse.failed(f"删除失败: {e}")
```

- [ ] **Step 2: 在 main.py 中注册路由**

在 `main.py` 中，找到 `pity.include_router(rag_router, ...)` 附近，添加：

```python
from app.routers.rag.kb_router import kb_router
pity.include_router(kb_router, dependencies=[Depends(request_info)])
```

- [ ] **Step 3: 验证语法**

Run:
```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && python3 -m py_compile app/routers/rag/kb_router.py
```

- [ ] **Step 4: 启动后端验证**

Run: `cd /Users/zhanzhicai/Desktop/py/pity/backend && python pity.py`
Expected: 服务正常启动，无报错

- [ ] **Step 5: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && git add app/routers/rag/kb_router.py main.py && git commit -m "feat: 新增知识库 CRUD 路由 (GET/POST/PUT/DELETE)"
```

---

## Task 5: 后端 — 修改现有 RAG 接口支持 lib_id

**Files:**
- Modify: `app/routers/rag/rag.py`
- Modify: `app/crud/knowledge_base/KnowledgeBaseDao.py`

- [ ] **Step 1: 修改 upload 端点，接受 lib_id 参数**

在 `rag.py` 的 `upload_document` 函数签名中，添加 `lib_id: int = Form(None)` 参数。
在保存到数据库时传入 `lib_id=lib_id`。

`upload_document` 函数签名改为：
```python
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    lib_id: int = Form(None),
    user_info: dict = Depends(get_current_user),
):
```

在 `KnowledgeBaseDao.insert_knowledge` 调用处添加 `lib_id=lib_id`。

- [ ] **Step 2: 修改 KnowledgeBaseDao.insert_knowledge，添加 lib_id 参数**

在 `KnowledgeBaseDao.py` 的 `insert_knowledge` 方法中：
- 添加 `lib_id=None` 参数
- 设置 `model.lib_id = lib_id`

- [ ] **Step 3: 修改 list_knowledge，添加 lib_id 筛选**

在 `KnowledgeBaseDao.py` 的 `list_knowledge` 方法中：
- 添加 `lib_id=None` 参数
- 在 kwargs 中添加 `lib_id` 筛选

在 `rag.py` 的 `list_documents` 函数中添加 `lib_id: Optional[int] = None` 参数并传入 DAO。

- [ ] **Step 4: 修改 search 端点，支持按知识库搜索**

在 `rag.py` 的 `search_knowledge` 函数中，从 body 提取 `lib_id` 和 `project_id`，传递给向量检索。

- [ ] **Step 5: 修改 KnowledgeBaseDao.list_knowledge 添加 lib_id 参数**

方法签名改为：
```python
async def list_knowledge(cls, page=1, size=20, name=None, status=None, lib_id=None, session=None):
    kwargs = {}
    if name:
        kwargs["name"] = name
    if status:
        kwargs["status"] = status
    if lib_id is not None:
        kwargs["lib_id"] = lib_id
    return await cls.list_with_pagination(page, size, session=session, **kwargs)
```

- [ ] **Step 6: 上传成功后更新知识库文档计数**

在 `upload_document` 函数末尾，上传成功后调用：
```python
if lib_id:
    await KnowledgeLibDao.update_document_count(lib_id)
```

- [ ] **Step 7: 验证语法并启动测试**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && python3 -m py_compile app/routers/rag/rag.py && python3 -m py_compile app/crud/knowledge_base/KnowledgeBaseDao.py
```

- [ ] **Step 8: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && git add app/routers/rag/rag.py app/crud/knowledge_base/KnowledgeBaseDao.py && git commit -m "feat: RAG 接口支持 lib_id 知识库关联"
```

---

## Task 6: 前端 — 路由 + 代理配置

**Files:**
- Modify: `pityweb2025AI/config/routes.ts`
- Modify: `pityweb2025AI/config/proxy.ts`

- [ ] **Step 1: 在 routes.ts 的 /ai 路由组中添加知识库路由**

在 `config/routes.ts` 中，找到 `/ai` 的 `routes` 数组，在 `/ai/task` 后面添加：

```typescript
{
  path: '/ai/knowledge',
  name: '知识库',
  component: './KnowledgeBase',
},
```

- [ ] **Step 2: 在 proxy.ts 中添加 /rag/ 代理**

在 `config/proxy.ts` 的 `dev` 对象中，添加 `/rag/` 代理条目：

```typescript
'/rag/': {
  target: 'http://0.0.0.0:7777',
  changeOrigin: true,
},
```

- [ ] **Step 3: 创建页面目录**

```bash
mkdir -p /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI/src/pages/KnowledgeBase/components
mkdir -p /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI/src/pages/KnowledgeBase/hooks
```

- [ ] **Step 4: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add config/routes.ts config/proxy.ts && git commit -m "feat: 添加知识库路由和 RAG 代理配置"
```

---

## Task 7: 前端 — 创建 services.js

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/services.js`

- [ ] **Step 1: 创建 API 调用文件**

```javascript
// src/pages/KnowledgeBase/services.js
import request from '@/utils/request';
import CONFIG from '@/consts/config';
import auth from '@/utils/auth';

// ==================== 知识库 CRUD ====================

export async function getKnowledgeBases(projectId) {
  return request(`${CONFIG.URL}/rag/knowledge-bases`, {
    method: 'GET',
    params: { project_id: projectId },
    headers: auth.headers(),
  });
}

export async function createKnowledgeBase(data) {
  return request(`${CONFIG.URL}/rag/knowledge-bases`, {
    method: 'POST',
    data,
    headers: auth.headers(),
  });
}

export async function updateKnowledgeBase(id, data) {
  return request(`${CONFIG.URL}/rag/knowledge-bases/${id}`, {
    method: 'PUT',
    data,
    headers: auth.headers(),
  });
}

export async function deleteKnowledgeBase(id) {
  return request(`${CONFIG.URL}/rag/knowledge-bases/${id}`, {
    method: 'DELETE',
    headers: auth.headers(),
  });
}

// ==================== 文档管理 ====================

export async function getDocuments(params) {
  return request(`${CONFIG.URL}/rag/list`, {
    method: 'GET',
    params,
    headers: auth.headers(),
  });
}

export async function uploadDocument(formData) {
  return request(`${CONFIG.URL}/rag/upload`, {
    method: 'POST',
    data: formData,
    headers: auth.headers(false),
  });
}

export async function deleteDocument(docId) {
  return request(`${CONFIG.URL}/rag/${docId}`, {
    method: 'DELETE',
    headers: auth.headers(),
  });
}

export async function getDocumentDetail(docId) {
  return request(`${CONFIG.URL}/rag/${docId}`, {
    method: 'GET',
    headers: auth.headers(),
  });
}

// ==================== 检索 ====================

export async function searchDocuments(data) {
  return request(`${CONFIG.URL}/rag/search`, {
    method: 'POST',
    data,
    headers: auth.headers(),
  });
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/services.js && git commit -m "feat: 知识库页面 API 服务层"
```

---

## Task 8: 前端 — 创建 Hooks

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/hooks/useKnowledgeBase.js`
- Create: `pityweb2025AI/src/pages/KnowledgeBase/hooks/useDocuments.js`

- [ ] **Step 1: 创建 useKnowledgeBase hook**

```javascript
// src/pages/KnowledgeBase/hooks/useKnowledgeBase.js
import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import auth from '@/utils/auth';
import {
  getKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
} from '../services';

export default function useKnowledgeBase(projectId) {
  const [list, setList] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);
  const [editingKB, setEditingKB] = useState(null);

  const fetchList = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await getKnowledgeBases(projectId);
      if (auth.response(res)) {
        setList(res.data || []);
        // 如果当前选中的不在列表中，清空选中
        if (currentId && !(res.data || []).find((item) => item.id === currentId)) {
          setCurrentId(null);
        }
      }
    } catch (e) {
      console.error('加载知识库列表失败', e);
    } finally {
      setLoading(false);
    }
  }, [projectId, currentId]);

  useEffect(() => {
    fetchList();
  }, [projectId]);

  const selectKB = useCallback((id) => {
    setCurrentId(id);
  }, []);

  const create = useCallback(async (data) => {
    const res = await createKnowledgeBase({ ...data, project_id: projectId });
    if (auth.response(res, true)) {
      setFormVisible(false);
      setEditingKB(null);
      await fetchList();
      // 自动选中新创建的
      if (res.data?.id) {
        setCurrentId(res.data.id);
      }
      return true;
    }
    return false;
  }, [projectId, fetchList]);

  const update = useCallback(async (id, data) => {
    const res = await updateKnowledgeBase(id, data);
    if (auth.response(res, true)) {
      setFormVisible(false);
      setEditingKB(null);
      await fetchList();
      return true;
    }
    return false;
  }, [fetchList]);

  const remove = useCallback(async (id) => {
    const res = await deleteKnowledgeBase(id);
    if (auth.response(res, true)) {
      if (currentId === id) {
        setCurrentId(null);
      }
      await fetchList();
      return true;
    }
    return false;
  }, [currentId, fetchList]);

  const openCreate = useCallback(() => {
    setEditingKB(null);
    setFormVisible(true);
  }, []);

  const openEdit = useCallback((kb) => {
    setEditingKB(kb);
    setFormVisible(true);
  }, []);

  const closeForm = useCallback(() => {
    setFormVisible(false);
    setEditingKB(null);
  }, []);

  // 当前选中的知识库对象
  const currentKB = list.find((item) => item.id === currentId) || null;

  return {
    list,
    currentId,
    currentKB,
    loading,
    formVisible,
    editingKB,
    fetchList,
    selectKB,
    create,
    update,
    remove,
    openCreate,
    openEdit,
    closeForm,
  };
}
```

- [ ] **Step 2: 创建 useDocuments hook**

```javascript
// src/pages/KnowledgeBase/hooks/useDocuments.js
import { useState, useEffect, useCallback } from 'react';
import auth from '@/utils/auth';
import {
  getDocuments,
  deleteDocument,
  getDocumentDetail,
  searchDocuments,
} from '../services';

export default function useDocuments(currentKB) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchAll, setSearchAll] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [searchResults, setSearchResults] = useState(null);

  const fetchList = useCallback(async () => {
    if (!currentKB) {
      setDocuments([]);
      return;
    }
    setLoading(true);
    try {
      const res = await getDocuments({ lib_id: currentKB.id, page: 1, size: 100 });
      if (auth.response(res)) {
        setDocuments(res.data?.list || []);
      }
    } catch (e) {
      console.error('加载文档列表失败', e);
    } finally {
      setLoading(false);
    }
  }, [currentKB]);

  useEffect(() => {
    fetchList();
    setSearchKeyword('');
    setSearchResults(null);
  }, [currentKB?.id]);

  const remove = useCallback(async (docId) => {
    const res = await deleteDocument(docId);
    if (auth.response(res, true)) {
      await fetchList();
      return true;
    }
    return false;
  }, [fetchList]);

  const showDetail = useCallback(async (docId) => {
    const res = await getDocumentDetail(docId);
    if (auth.response(res)) {
      setDetailData(res.data);
      setDetailVisible(true);
    }
  }, []);

  const closeDetail = useCallback(() => {
    setDetailVisible(false);
    setDetailData(null);
  }, []);

  const search = useCallback(async (keyword, projectId) => {
    if (!keyword?.trim()) {
      setSearchResults(null);
      return;
    }
    setLoading(true);
    try {
      const data = { query: keyword, top_k: 20 };
      if (searchAll && projectId) {
        data.project_id = projectId;
      } else if (currentKB) {
        data.lib_id = currentKB.id;
      }
      const res = await searchDocuments(data);
      if (auth.response(res)) {
        setSearchResults(res.data);
      }
    } catch (e) {
      console.error('检索失败', e);
    } finally {
      setLoading(false);
    }
  }, [currentKB, searchAll]);

  const resetSearch = useCallback(() => {
    setSearchKeyword('');
    setSearchResults(null);
  }, []);

  // 文档统计
  const stats = {
    total: documents.length,
    ready: documents.filter((d) => d.status === 'ready').length,
    processing: documents.filter((d) => d.status === 'processing').length,
    error: documents.filter((d) => d.status === 'error').length,
  };

  return {
    documents,
    loading,
    searchKeyword,
    searchAll,
    detailVisible,
    detailData,
    searchResults,
    stats,
    fetchList,
    remove,
    showDetail,
    closeDetail,
    search,
    setSearchKeyword,
    setSearchAll,
    resetSearch,
  };
}
```

- [ ] **Step 3: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/hooks/ && git commit -m "feat: 知识库 hooks (useKnowledgeBase + useDocuments)"
```

---

## Task 9: 前端 — 创建 KnowledgeBaseForm 弹窗

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/components/KnowledgeBaseForm.jsx`

- [ ] **Step 1: 创建新建/编辑知识库弹窗组件**

```jsx
// src/pages/KnowledgeBase/components/KnowledgeBaseForm.jsx
import React, { useEffect } from 'react';
import { Form, Input, InputNumber, Modal } from 'antd';

export default function KnowledgeBaseForm({ visible, editingKB, onSave, onCancel }) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible) {
      if (editingKB) {
        form.setFieldsValue({
          name: editingKB.name,
          description: editingKB.description,
          chunk_size: editingKB.chunk_size || 500,
          overlap: editingKB.overlap || 50,
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, editingKB]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onSave(values);
    } catch {
      // 表单校验失败
    }
  };

  return (
    <Modal
      title={editingKB ? '编辑知识库' : '新建知识库'}
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      okText="保存"
      cancelText="取消"
      width={520}
      destroyOnClose
    >
      <Form form={form} labelCol={{ span: 6 }} wrapperCol={{ span: 16 }}>
        <Form.Item
          label="名称"
          name="name"
          rules={[{ required: true, message: '请输入知识库名称' }, { max: 50 }]}
        >
          <Input placeholder="请输入知识库名称" />
        </Form.Item>
        <Form.Item
          label="描述"
          name="description"
          rules={[{ max: 200 }]}
        >
          <Input.TextArea rows={3} placeholder="请输入描述" />
        </Form.Item>
        <Form.Item
          label="分块大小"
          name="chunk_size"
          initialValue={500}
          rules={[{ required: true }]}
        >
          <InputNumber min={100} max={2000} step={100} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          label="重叠大小"
          name="overlap"
          initialValue={50}
          rules={[{ required: true }]}
        >
          <InputNumber min={0} max={500} step={10} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/components/KnowledgeBaseForm.jsx && git commit -m "feat: 知识库新建/编辑弹窗组件"
```

---

## Task 10: 前端 — 创建 KnowledgeBaseList 组件

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/components/KnowledgeBaseList.jsx`

- [ ] **Step 1: 创建左侧知识库列表组件**

```jsx
// src/pages/KnowledgeBase/components/KnowledgeBaseList.jsx
import React, { useState } from 'react';
import { Button, Dropdown, Empty, Input, List, Popconfirm, Space, Tag } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EllipsisOutlined,
} from '@ant-design/icons';

const styles = {
  container: { padding: '12px' },
  listItem: {
    padding: '8px 12px',
    cursor: 'pointer',
    borderRadius: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
    transition: 'background 0.2s',
  },
  listItemActive: {
    background: '#e6f7ff',
    borderLeft: '3px solid #1677ff',
  },
  listItemHover: {
    background: '#f5f5f5',
  },
};

export default function KnowledgeBaseList({
  list,
  currentId,
  loading,
  onSelect,
  onEdit,
  onDelete,
  onCreate,
}) {
  const [searchText, setSearchText] = useState('');

  const filteredList = list.filter((item) =>
    item.name?.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <div style={styles.container}>
      <Input.Search
        placeholder="搜索知识库"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 8 }}
        allowClear
      />
      <Button
        type="primary"
        icon={<PlusOutlined />}
        block
        onClick={onCreate}
        style={{ marginBottom: 12 }}
      >
        新建知识库
      </Button>

      {filteredList.length === 0 ? (
        <Empty description="暂无知识库" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          loading={loading}
          dataSource={filteredList}
          renderItem={(item) => (
            <KnowledgeBaseItem
              key={item.id}
              item={item}
              active={item.id === currentId}
              onSelect={onSelect}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          )}
        />
      )}
    </div>
  );
}

function KnowledgeBaseItem({ item, active, onSelect, onEdit, onDelete }) {
  const [hovered, setHovered] = useState(false);

  const menuItems = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑',
      onClick: (e) => {
        e.domEvent?.stopPropagation();
        onEdit(item);
      },
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true,
      onClick: (e) => {
        e.domEvent?.stopPropagation();
      },
    },
  ];

  return (
    <div
      style={{
        ...styles.listItem,
        ...(active ? styles.listItemActive : {}),
        ...(hovered && !active ? styles.listItemHover : {}),
      }}
      onClick={() => onSelect(item.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {item.name}
        </div>
        <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
          {item.document_count || 0} 篇文档
        </div>
      </div>
      {(hovered || active) && (
        <Dropdown menu={{ items: menuItems }} trigger={['click']}>
          <EllipsisOutlined
            style={{ fontSize: 16, color: '#999', cursor: 'pointer', padding: '0 4px' }}
            onClick={(e) => e.stopPropagation()}
          />
        </Dropdown>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/components/KnowledgeBaseList.jsx && git commit -m "feat: 知识库列表组件（含 hover 编辑/删除）"
```

---

## Task 11: 前端 — 创建 DocumentTable 组件

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/components/DocumentTable.jsx`

- [ ] **Step 1: 创建右侧文档表格组件**

```jsx
// src/pages/KnowledgeBase/components/DocumentTable.jsx
import React from 'react';
import {
  Badge,
  Button,
  Checkbox,
  Empty,
  Input,
  Popconfirm,
  Space,
  Table,
  Tag,
} from 'antd';
import { UploadOutlined, ReloadOutlined, SearchOutlined, UndoOutlined } from '@ant-design/icons';
import moment from 'moment';

const FILE_TYPE_COLORS = {
  pdf: 'blue',
  docx: 'purple',
  md: 'orange',
  txt: 'default',
};

const STATUS_MAP = {
  pending: { text: '待处理', status: 'warning' },
  processing: { text: '处理中', status: 'processing' },
  ready: { text: '就绪', status: 'success' },
  error: { text: '错误', status: 'error' },
};

function formatFileSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export default function DocumentTable({
  currentKB,
  documents,
  loading,
  stats,
  searchKeyword,
  searchAll,
  onSearchKeywordChange,
  onSearchAllChange,
  onSearch,
  onReset,
  onUpload,
  onRefresh,
  onView,
  onDelete,
}) {
  if (!currentKB) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Empty description="请选择左侧知识库查看文档" />
      </div>
    );
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 80,
      render: (type) => {
        const ext = (type || '').split('/').pop()?.toLowerCase() || type;
        return <Tag color={FILE_TYPE_COLORS[ext] || 'default'}>{ext?.toUpperCase()}</Tag>;
      },
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 80,
      render: (size) => formatFileSize(size),
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 70,
      render: (v) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const s = STATUS_MAP[status] || { text: status, status: 'default' };
        return <Badge status={s.status} text={s.text} />;
      },
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (v) => (v ? moment(v).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <a onClick={() => onView(record.id)}>查看</a>
          <Popconfirm title="确定删除该文档？" onConfirm={() => onDelete(record.id)}>
            <a style={{ color: '#ff4d4f' }}>删除</a>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 16 }}>
      {/* 知识库信息栏 */}
      <div style={{ marginBottom: 12, borderBottom: '1px solid #f0f0f0', paddingBottom: 12 }}>
        <h3 style={{ margin: 0 }}>{currentKB.name}</h3>
        {currentKB.description && (
          <div style={{ color: '#999', fontSize: 13, marginTop: 4 }}>{currentKB.description}</div>
        )}
        <div style={{ marginTop: 8 }}>
          <Space>
            <Tag>文档: {stats.total}</Tag>
            <Tag color="green">已处理: {stats.ready}</Tag>
            {stats.error > 0 && <Tag color="red">失败: {stats.error}</Tag>}
          </Space>
        </div>
      </div>

      {/* 操作栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <Space>
          <Input.Search
            placeholder="搜索文档关键词"
            value={searchKeyword}
            onChange={(e) => onSearchKeywordChange(e.target.value)}
            onSearch={() => onSearch(searchKeyword)}
            style={{ width: 220 }}
            allowClear
          />
          <Checkbox checked={searchAll} onChange={(e) => onSearchAllChange(e.target.checked)}>
            搜索全部知识库
          </Checkbox>
        </Space>
        <Space>
          <Button icon={<UploadOutlined />} onClick={onUpload}>上传文档</Button>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>刷新</Button>
          <Button type="primary" icon={<SearchOutlined />} onClick={() => onSearch(searchKeyword)}>
            查询
          </Button>
          <Button icon={<UndoOutlined />} onClick={onReset}>重置</Button>
        </Space>
      </div>

      {/* 文档表格 */}
      <Table
        columns={columns}
        dataSource={documents}
        loading={loading}
        rowKey="id"
        size="small"
        bordered
        pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
      />
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/components/DocumentTable.jsx && git commit -m "feat: 文档表格组件（含搜索、筛选、操作栏）"
```

---

## Task 12: 前端 — 创建 DocumentUpload + DocumentDetail 组件

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/components/DocumentUpload.jsx`
- Create: `pityweb2025AI/src/pages/KnowledgeBase/components/DocumentDetail.jsx`

- [ ] **Step 1: 创建上传弹窗**

```jsx
// src/pages/KnowledgeBase/components/DocumentUpload.jsx
import React, { useState } from 'react';
import { InboxOutlined, Modal, Upload, message } from 'antd';
import { uploadDocument } from '../services';
import auth from '@/utils/auth';

const { Dragger } = Upload;

const ACCEPT_TYPES = '.pdf,.docx,.md,.txt';

export default function DocumentUpload({ visible, currentKB, onSuccess, onCancel }) {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请选择要上传的文件');
      return;
    }
    setUploading(true);
    let successCount = 0;
    for (const file of fileList) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name);
      if (currentKB?.id) {
        formData.append('lib_id', currentKB.id);
      }
      try {
        const res = await uploadDocument(formData);
        if (auth.response(res)) {
          successCount++;
        }
      } catch (e) {
        console.error('上传失败', e);
      }
    }
    setUploading(false);
    if (successCount > 0) {
      message.success(`成功上传 ${successCount} 个文件`);
      setFileList([]);
      onSuccess?.();
    }
  };

  const beforeUpload = (file) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    const allowed = ['pdf', 'docx', 'md', 'txt'];
    if (!allowed.includes(ext)) {
      message.error(`不支持的文件类型: .${ext}`);
      return Upload.LIST_IGNORE;
    }
    setFileList((prev) => [...prev, file]);
    return false;
  };

  const handleRemove = (file) => {
    setFileList((prev) => prev.filter((f) => f !== file));
  };

  return (
    <Modal
      title="上传文档"
      open={visible}
      onOk={handleUpload}
      onCancel={() => { setFileList([]); onCancel(); }}
      okText="上传"
      cancelText="关闭"
      confirmLoading={uploading}
      width={600}
      destroyOnClose
    >
      <Dragger
        multiple
        accept={ACCEPT_TYPES}
        fileList={fileList}
        beforeUpload={beforeUpload}
        onRemove={handleRemove}
      >
        <p style={{ fontSize: 48, color: '#1677ff', marginBottom: 8 }}>
          <InboxOutlined />
        </p>
        <p>点击或拖拽文件到此区域上传</p>
        <p style={{ color: '#999', fontSize: 12 }}>
          支持 PDF、DOCX、Markdown、TXT 格式
        </p>
      </Dragger>
    </Modal>
  );
}
```

- [ ] **Step 2: 创建文档详情抽屉**

```jsx
// src/pages/KnowledgeBase/components/DocumentDetail.jsx
import React from 'react';
import { Alert, Badge, Collapse, Descriptions, Drawer, Tag, Typography } from 'antd';
import moment from 'moment';

const { Paragraph } = Typography;

const STATUS_MAP = {
  pending: { text: '待处理', status: 'warning' },
  processing: { text: '处理中', status: 'processing' },
  ready: { text: '就绪', status: 'success' },
  error: { text: '错误', status: 'error' },
};

function formatFileSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export default function DocumentDetail({ visible, data, onClose }) {
  if (!data) return null;

  const statusInfo = STATUS_MAP[data.status] || { text: data.status, status: 'default' };

  return (
    <Drawer title="文档详情" width={640} open={visible} onClose={onClose} destroyOnClose>
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="文档名称" span={2}>{data.name}</Descriptions.Item>
        <Descriptions.Item label="文件类型">
          <Tag>{data.file_type}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="文件大小">{formatFileSize(data.file_size)}</Descriptions.Item>
        <Descriptions.Item label="分块数量">{data.chunk_count || 0}</Descriptions.Item>
        <Descriptions.Item label="状态">
          <Badge status={statusInfo.status} text={statusInfo.text} />
        </Descriptions.Item>
        <Descriptions.Item label="上传时间" span={2}>
          {data.created_at ? moment(data.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
        </Descriptions.Item>
        {data.status === 'error' && data.error_msg && (
          <Descriptions.Item label="错误信息" span={2}>
            <Alert type="error" message={data.error_msg} showIcon />
          </Descriptions.Item>
        )}
      </Descriptions>

      {/* 分块预览 - 暂时显示提示，后续接入分块 API */}
      <div style={{ marginTop: 16 }}>
        <h4>分块预览</h4>
        <div style={{ color: '#999', textAlign: 'center', padding: 24 }}>
          共 {data.chunk_count || 0} 个分块，预览功能开发中...
        </div>
      </div>
    </Drawer>
  );
}
```

- [ ] **Step 3: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/components/DocumentUpload.jsx src/pages/KnowledgeBase/components/DocumentDetail.jsx && git commit -m "feat: 文档上传弹窗和详情抽屉组件"
```

---

## Task 13: 前端 — 组装主页面 KnowledgeBase.jsx

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/index.jsx`

- [ ] **Step 1: 创建主布局页面**

```jsx
// src/pages/KnowledgeBase/index.jsx
import React, { useState } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Card, Select, Space, Spin } from 'antd';
import SplitPane from 'react-split-pane';
import ScrollCard from '@/components/Scrollbar/ScrollCard';
import { useProject } from '@/utils/useProject';
import useKnowledgeBase from './hooks/useKnowledgeBase';
import useDocuments from './hooks/useDocuments';
import KnowledgeBaseList from './components/KnowledgeBaseList';
import DocumentTable from './components/DocumentTable';
import KnowledgeBaseForm from './components/KnowledgeBaseForm';
import DocumentUpload from './components/DocumentUpload';
import DocumentDetail from './components/DocumentDetail';

export default function KnowledgeBase() {
  const { projects, loading: projectLoading } = useProject();
  const [projectId, setProjectId] = useState(null);

  const kb = useKnowledgeBase(projectId);
  const docs = useDocuments(kb.currentKB);

  const [uploadVisible, setUploadVisible] = useState(false);

  // 处理表单保存
  const handleFormSave = async (values) => {
    if (kb.editingKB) {
      return kb.update(kb.editingKB.id, values);
    }
    return kb.create(values);
  };

  // 处理知识库删除（带确认）
  const handleDeleteKB = (item) => {
    kb.remove(item.id);
  };

  return (
    <PageContainer>
      <Card>
        {/* 项目选择器 */}
        <div style={{ marginBottom: 12 }}>
          <Space>
            <span>项目：</span>
            <Select
              style={{ width: 300 }}
              placeholder="请选择项目"
              loading={projectLoading}
              value={projectId}
              onChange={setProjectId}
              showSearch
              optionFilterProp="label"
              options={(projects || []).map((p) => ({
                value: p.id,
                label: p.name,
              }))}
            />
          </Space>
        </div>

        <SplitPane split="vertical" defaultSize={280} minSize={200} maxSize={400}>
          {/* 左侧：知识库列表 */}
          <ScrollCard>
            <KnowledgeBaseList
              list={kb.list}
              currentId={kb.currentId}
              loading={kb.loading}
              onSelect={kb.selectKB}
              onEdit={kb.openEdit}
              onDelete={handleDeleteKB}
              onCreate={kb.openCreate}
            />
          </ScrollCard>

          {/* 右侧：文档管理 */}
          <ScrollCard>
            <DocumentTable
              currentKB={kb.currentKB}
              documents={docs.documents}
              loading={docs.loading}
              stats={docs.stats}
              searchKeyword={docs.searchKeyword}
              searchAll={docs.searchAll}
              onSearchKeywordChange={docs.setSearchKeyword}
              onSearchAllChange={docs.setSearchAll}
              onSearch={(keyword) => docs.search(keyword, projectId)}
              onReset={docs.resetSearch}
              onUpload={() => setUploadVisible(true)}
              onRefresh={docs.fetchList}
              onView={docs.showDetail}
              onDelete={docs.remove}
            />
          </ScrollCard>
        </SplitPane>

        {/* 新建/编辑知识库弹窗 */}
        <KnowledgeBaseForm
          visible={kb.formVisible}
          editingKB={kb.editingKB}
          onSave={handleFormSave}
          onCancel={kb.closeForm}
        />

        {/* 上传文档弹窗 */}
        <DocumentUpload
          visible={uploadVisible}
          currentKB={kb.currentKB}
          onSuccess={docs.fetchList}
          onCancel={() => setUploadVisible(false)}
        />

        {/* 文档详情抽屉 */}
        <DocumentDetail
          visible={docs.detailVisible}
          data={docs.detailData}
          onClose={docs.closeDetail}
        />
      </Card>
    </PageContainer>
  );
}
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/index.jsx && git commit -m "feat: 知识库主页面（SplitPane 布局 + 项目选择器）"
```

---

## Task 14: 前端 — SplitPane 样式修复

**Files:**
- Create: `pityweb2025AI/src/pages/KnowledgeBase/index.less`（如需要）

- [ ] **Step 1: 添加 SplitPane 最小高度样式**

如果 SplitPane 高度不正确，在页面组件中添加全局样式或在 index.less 中处理：

```css
/* 如果需要创建 index.less */
.Pane1,
.Pane2 {
  overflow: auto;
}
```

在 `index.jsx` 中引入：`import './index.less';`（如果创建了样式文件）

- [ ] **Step 2: 验证页面渲染**

Run: `cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && npm run start:dev`
Expected: 访问 `http://localhost:8000/#/ai/knowledge` 能看到知识库页面

- [ ] **Step 3: 提交**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add src/pages/KnowledgeBase/ && git commit -m "feat: 知识库页面样式修复"
```

---

## Task 15: 集成测试

- [ ] **Step 1: 后端启动验证**

```bash
cd /Users/zhanzhicai/Desktop/py/pity/backend && python pity.py
```

验证：
- 服务正常启动，`knowledge_lib` 表自动创建
- `knowledge_base` 表新增 `lib_id` 列

- [ ] **Step 2: 后端 API 测试**

使用 Swagger（`http://localhost:7777/docs`）或 curl 测试：

```bash
# 创建知识库
curl -X POST http://localhost:7777/rag/knowledge-bases \
  -H "token: <pityToken>" \
  -H "Content-Type: application/json" \
  -d '{"name":"测试知识库","project_id":1}'

# 列出知识库
curl http://localhost:7777/rag/knowledge-bases?project_id=1 \
  -H "token: <pityToken>"

# 上传文档
curl -X POST http://localhost:7777/rag/upload \
  -H "token: <pityToken>" \
  -F "file=@test.txt" \
  -F "name=测试文档" \
  -F "lib_id=1"

# 列出文档
curl "http://localhost:7777/rag/list?lib_id=1" \
  -H "token: <pityToken>"
```

- [ ] **Step 3: 前端功能测试**

访问 `http://localhost:8000/#/ai/knowledge`，测试：

| 操作 | 预期结果 |
|------|---------|
| 选择项目 | 左侧加载该项目的知识库列表 |
| 点击"新建知识库" | 弹出新建弹窗，填写保存后列表刷新 |
| 点击知识库项 | 右侧加载该知识库文档列表 |
| hover 知识库项 → 编辑 | 弹出编辑弹窗，修改后列表更新 |
| hover 知识库项 → 删除 | 删除后列表更新 |
| 上传文档 | 拖拽上传，成功后文档列表刷新 |
| 查看文档详情 | 右侧弹出详情抽屉 |
| 删除文档 | 确认后文档列表刷新 |
| 搜索关键词 | 过滤文档列表或调用检索 API |
| 勾选"搜索全部知识库" | 跨知识库搜索 |

- [ ] **Step 4: 最终提交**

```bash
# 后端
cd /Users/zhanzhicai/Desktop/py/pity/backend && git add -A && git commit -m "feat: Phase 知识库管理前后端联调完成"

# 前端
cd /Users/zhanzhicai/Desktop/py/pity/pityweb2025AI && git add -A && git commit -m "feat: Phase 知识库管理前后端联调完成"
```

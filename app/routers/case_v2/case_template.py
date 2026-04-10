"""
动态模板用例路由
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.handler.fatcory import PityResponse
from app.routers import Permission, get_session
from app.schema.testcase_template import TestcaseTemplateSchema
from app.schema.case_v2 import CaseV2Schema, CaseV2WithFieldsSchema
from app.schema.ai_generation_task import AIGenerationTaskSchema, AIGenerationTaskUpdateSchema
from app.models.testcase_template import PityTestcaseTemplate
from app.models.case_v2 import PityCaseV2
from app.models.case_field import PityTestcaseField
from app.crud.testcase_template.TestcaseTemplateDao import TestcaseTemplateDao
from app.crud.case_v2.CaseV2Dao import CaseV2Dao
from sqlalchemy import select, func

router = APIRouter(prefix='/case/v2', tags=['动态模板用例'])


# ============== 模板管理 ==============

@router.get('/template/list')
async def list_template(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        test_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        user_info: dict = Depends(Permission()),
):
    """获取模板列表"""
    where = {}
    if test_type:
        where["test_type"] = test_type
    if is_active is not None:
        where["is_active"] = is_active

    data, total = await TestcaseTemplateDao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('/template')
async def get_template(id: int = Query(...)):
    """获取单个模板"""
    record = await TestcaseTemplateDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='模板不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.post('/template')
async def create_template(data: TestcaseTemplateSchema, user_info: dict = Depends(Permission())):
    """创建模板"""
    model = PityTestcaseTemplate(
        name=data.name,
        description=data.description,
        test_type=data.test_type,
        source=data.source,
        field_mapping=data.field_mapping,
        is_default=data.is_default,
        is_active=data.is_active,
        create_user=user_info['id'],
    )
    result = await TestcaseTemplateDao.insert(model=model, log=True)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.put('/template')
async def update_template(data: TestcaseTemplateSchema, user_info: dict = Depends(Permission())):
    """更新模板"""
    await TestcaseTemplateDao.update_by_map(
        user_info['id'],
        PityTestcaseTemplate.id == data.id,
        name=data.name,
        description=data.description,
        test_type=data.test_type,
        source=data.source,
        field_mapping=data.field_mapping,
        is_default=data.is_default,
        is_active=data.is_active,
    )
    result = await TestcaseTemplateDao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('/template')
async def delete_template(id: int = Query(...), user_info: dict = Depends(Permission()),
                          session=Depends(get_session)):
    """删除模板"""
    await TestcaseTemplateDao.delete_record_by_id(session, user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


# ============== 用例管理 ==============

@router.get('/list')
async def list_case(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        template_id: Optional[int] = None,
        case_type: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[int] = None,
        user_info: dict = Depends(Permission()),
):
    """获取用例列表"""
    where = {}
    if template_id is not None:
        where["template_id"] = template_id
    if case_type:
        where["case_type"] = case_type
    if source:
        where["source"] = source
    if status is not None:
        where["status"] = status

    data, total = await CaseV2Dao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('')
async def get_case(id: int = Query(...)):
    """获取单个用例（包含扩展字段）"""
    case = await CaseV2Dao.query_record(id=id)
    if not case:
        return PityResponse.failed(msg='用例不存在')

    # 查询扩展字段
    from app.crud import async_session
    async with async_session() as session:
        stmt = select(PityTestcaseField).where(PityTestcaseField.case_id == id)
        result = await session.execute(stmt)
        fields = result.scalars().all()

    case_dict = PityResponse.model_to_dict(case)
    case_dict['fields'] = [PityResponse.model_to_dict(f) for f in fields]
    return PityResponse.success(case_dict)


@router.post('')
async def create_case(data: CaseV2WithFieldsSchema, user_info: dict = Depends(Permission())):
    """创建用例"""
    model = PityCaseV2(
        name=data.name,
        case_no=data.case_no,
        priority=data.priority,
        status=data.status,
        directory_id=data.directory_id,
        tag=data.tag,
        template_id=data.template_id,
        case_type=data.case_type,
        source=data.source,
        preconditions=data.preconditions,
        expected_result=data.expected_result,
        test_steps=data.test_steps,
        create_user=user_info['id'],
    )
    result = await CaseV2Dao.insert(model=model, log=True)

    # 插入扩展字段
    if data.fields:
        from app.models.case_field import PityTestcaseField
        for field in data.fields:
            field_model = PityTestcaseField(
                case_id=result.id,
                field_name=field.get('field_name'),
                field_value=field.get('field_value'),
                create_user=user_info['id'],
            )
            from app.crud import async_session
            async with async_session() as session:
                session.add(field_model)
                await session.commit()

    return PityResponse.success(PityResponse.model_to_dict(result))


@router.put('')
async def update_case(data: CaseV2WithFieldsSchema, user_info: dict = Depends(Permission())):
    """更新用例"""
    await CaseV2Dao.update_by_map(
        user_info['id'],
        PityCaseV2.id == data.id,
        name=data.name,
        case_no=data.case_no,
        priority=data.priority,
        status=data.status,
        directory_id=data.directory_id,
        tag=data.tag,
        template_id=data.template_id,
        case_type=data.case_type,
        source=data.source,
        preconditions=data.preconditions,
        expected_result=data.expected_result,
        test_steps=data.test_steps,
    )

    # 更新扩展字段（先删后插）
    if data.fields:
        from app.models.case_field import PityTestcaseField
        from app.crud import async_session
        async with async_session() as session:
            # 删除旧字段
            await session.execute(
                PityTestcaseField.__table__.delete().where(PityTestcaseField.case_id == data.id)
            )
            # 插入新字段
            for field in data.fields:
                field_model = PityTestcaseField(
                    case_id=data.id,
                    field_name=field.get('field_name'),
                    field_value=field.get('field_value'),
                    create_user=user_info['id'],
                )
                session.add(field_model)
            await session.commit()

    result = await CaseV2Dao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('')
async def delete_case(id: int = Query(...), user_info: dict = Depends(Permission()),
                     session=Depends(get_session)):
    """删除用例"""
    # 先删除扩展字段
    from app.models.case_field import PityTestcaseField
    await session.execute(
        PityTestcaseField.__table__.delete().where(PityTestcaseField.case_id == id)
    )
    await session.commit()

    await CaseV2Dao.delete_record_by_id(session, user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


# ============== AI 生成任务管理 ==============

@router.get('/ai/task/list')
async def list_ai_task(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        user_info: dict = Depends(Permission()),
):
    """获取 AI 生成任务列表"""
    where = {}
    if project_id is not None:
        where["project_id"] = project_id
    if status:
        where["status"] = status

    from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
    data, total = await AIGenerationTaskDao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('/ai/task')
async def get_ai_task(id: int = Query(...)):
    """获取单个 AI 生成任务"""
    from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
    record = await AIGenerationTaskDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='任务不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.post('/ai/task')
async def create_ai_task(data: AIGenerationTaskSchema, user_info: dict = Depends(Permission())):
    """创建 AI 生成任务"""
    from app.models.ai_generation_task import PityAIGenerationTask
    from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao

    model = PityAIGenerationTask(
        name=data.name,
        project_id=data.project_id,
        template_id=data.template_id,
        case_type=data.case_type,
        requirement=data.requirement,
        source=data.source or 'ai',
        create_user=user_info['id'],
    )
    result = await AIGenerationTaskDao.insert(model=model, log=True)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.post('/ai/task/execute')
async def execute_ai_task(id: int = Query(...), user_info: dict = Depends(Permission())):
    """执行 AI 生成任务"""
    from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
    from app.core.ai.case_generator import AIGenerationWorkflow

    # 获取任务
    task = await AIGenerationTaskDao.query_record(id=id)
    if not task:
        return PityResponse.failed(msg='任务不存在')

    # 执行工作流（异步，实际使用 Celery）
    # 这里简化处理，实际应该触发 Celery 任务
    try:
        workflow = AIGenerationWorkflow(user_id=user_info['id'])
        result = await workflow.execute(id)
        return PityResponse.success(result)
    except Exception as e:
        return PityResponse.failed(msg=f'执行失败: {e}')


@router.put('/ai/task')
async def update_ai_task(data: AIGenerationTaskUpdateSchema, user_info: dict = Depends(Permission())):
    """更新 AI 生成任务"""
    from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
    from app.models.ai_generation_task import PityAIGenerationTask

    update_data = {k: v for k, v in data.model_dump().items() if v is not None and k != 'id'}
    if update_data:
        await AIGenerationTaskDao.update_by_map(
            user_info['id'],
            PityAIGenerationTask.id == data.id,
            **update_data
        )
    result = await AIGenerationTaskDao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('/ai/task')
async def delete_ai_task(id: int = Query(...), user_info: dict = Depends(Permission()),
                       session=Depends(get_session)):
    """删除 AI 生成任务"""
    from app.crud.ai_generation_task.AIGenerationTaskDao import AIGenerationTaskDao
    await AIGenerationTaskDao.delete_record_by_id(session, user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


# ============== 测试查询（验证 JOIN 扩展表速度） ==============

@router.get('/test/join')
async def test_join_query(
        case_type: Optional[str] = Query(None),
        user_info: dict = Depends(Permission()),
):
    """测试 JOIN 扩展表查询"""
    from app.crud import async_session
    from sqlalchemy import select, text

    # 原始 SQL 查询
    sql = """
        SELECT c.*, f.field_name, f.field_value
        FROM pity_case_v2 c
        LEFT JOIN pity_testcase_field f ON c.id = f.case_id
        WHERE 1=1
    """
    if case_type:
        sql += f" AND c.case_type = '{case_type}'"

    async with async_session() as session:
        result = await session.execute(text(sql))
        rows = result.fetchall()

    return PityResponse.success(data=[dict(row._mapping) for row in rows])

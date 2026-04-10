"""
Phase X 路由 - 独立的测试调度体系
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.handler.fatcory import PityResponse
from app.routers import Permission, get_session
from app.schema.phasex import (
    PhaseXPlanSchema, PhaseXPlanUpdateSchema,
    PhaseXExecutionSchema
)
from app.models.phasex import PityPhaseXPlan, PityPhaseXExecution
from app.crud.phasex import PityPhaseXPlanDao, PityPhaseXExecutionDao, PityPhaseXReportDao
from app.schema.phasex import PhaseXReportSchema
from app.models.phasex import PityPhaseXReport

router = APIRouter(prefix='/phasex', tags=['Phase X 测试'])


# ============== 测试计划 ==============

@router.get('/plan/list')
async def list_plan(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        project_id: Optional[int] = None,
        plan_type: Optional[str] = None,
        is_active: Optional[int] = None,
        user_info: dict = Depends(Permission()),
):
    """获取测试计划列表"""
    where = {}
    if project_id is not None:
        where["project_id"] = project_id
    if plan_type:
        where["plan_type"] = plan_type
    if is_active is not None:
        where["is_active"] = is_active

    data, total = await PityPhaseXPlanDao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('/plan')
async def get_plan(id: int = Query(...)):
    """获取单个测试计划"""
    record = await PityPhaseXPlanDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='计划不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.post('/plan')
async def create_plan(data: PhaseXPlanSchema, user_info: dict = Depends(Permission())):
    """创建测试计划"""
    model = PityPhaseXPlan(
        name=data.name,
        description=data.description,
        project_id=data.project_id,
        plan_type=data.plan_type,
        target_id=data.target_id,
        target_name=data.target_name,
        environment_id=data.environment_id,
        cron_expression=data.cron_expression,
        is_periodic=data.is_periodic,
        config=data.config,
        is_active=data.is_active,
        tags=data.tags,
        create_user=user_info['id'],
    )
    result = await PityPhaseXPlanDao.insert(model=model, log=True)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.put('/plan')
async def update_plan(data: PhaseXPlanUpdateSchema, user_info: dict = Depends(Permission())):
    """更新测试计划"""
    update_data = {k: v for k, v in data.model_dump().items()
                  if v is not None and k != 'id'}
    if update_data:
        await PityPhaseXPlanDao.update_by_map(
            user_info['id'],
            PityPhaseXPlan.id == data.id,
            **update_data
        )
    result = await PityPhaseXPlanDao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('/plan')
async def delete_plan(id: int = Query(...), user_info: dict = Depends(Permission()),
                     session=Depends(get_session)):
    """删除测试计划"""
    await PityPhaseXPlanDao.delete_record_by_id(session, user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


@router.post('/plan/execute')
async def execute_plan(id: int = Query(...), user_info: dict = Depends(Permission())):
    """手动执行测试计划"""
    # 获取计划信息
    plan = await PityPhaseXPlanDao.query_record(id=id)
    if not plan:
        return PityResponse.failed(msg='计划不存在')

    # 触发 Celery 异步任务
    from app.tasks.phasex_tasks import execute_plan as celery_execute_plan
    task = celery_execute_plan.delay(plan_id=id, user_id=user_info['id'])
    return PityResponse.success({
        "message": "执行已触发",
        "plan_id": id,
        "task_id": task.id
    })


# ============== 执行记录 ==============

@router.get('/execution/list')
async def list_execution(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        plan_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        user_info: dict = Depends(Permission()),
):
    """获取执行记录列表"""
    where = {}
    if plan_id is not None:
        where["plan_id"] = plan_id
    if project_id is not None:
        where["project_id"] = project_id
    if status:
        where["status"] = status

    data, total = await PityPhaseXExecutionDao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('/execution')
async def get_execution(id: int = Query(...)):
    """获取执行记录详情"""
    record = await PityPhaseXExecutionDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='执行记录不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.get('/execution/latest')
async def get_latest_execution(
        plan_id: int = Query(...),
        user_info: dict = Depends(Permission()),
):
    """获取计划的最新执行记录"""
    from sqlalchemy import select
    from app.crud import async_session
    async with async_session() as session:
        stmt = select(PityPhaseXExecution).where(
            PityPhaseXExecution.plan_id == plan_id,
            PityPhaseXExecution.deleted_at == 0
        ).order_by(PityPhaseXExecution.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        record = result.scalars().first()

    if not record:
        return PityResponse.failed(msg='暂无执行记录')
    return PityResponse.success(PityResponse.model_to_dict(record))


# ============== 测试报告 ==============

@router.get('/report/list')
async def list_report(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        project_id: Optional[int] = None,
        user_info: dict = Depends(Permission()),
):
    """获取测试报告列表"""
    where = {}
    if project_id is not None:
        where["project_id"] = project_id

    data, total = await PityPhaseXReportDao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('/report')
async def get_report(id: int = Query(...)):
    """获取测试报告详情"""
    record = await PityPhaseXReportDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='报告不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.post('/report')
async def create_or_update_report(data: PhaseXReportSchema, user_info: dict = Depends(Permission())):
    """创建或更新测试报告"""
    if data.id:
        # 更新
        update_data = {k: v for k, v in data.model_dump().items() if v is not None and k != 'id'}
        if update_data:
            await PityPhaseXReportDao.update_by_map(
                user_info['id'],
                PityPhaseXReport.id == data.id,
                **update_data
            )
        result = await PityPhaseXReportDao.query_record(id=data.id)
    else:
        # 创建
        model = PityPhaseXReport(
            name=data.name,
            project_id=data.project_id,
            total_runs=data.total_runs or 0,
            total_passed=data.total_passed or 0,
            total_failed=data.total_failed or 0,
            total_error=data.total_error or 0,
            trend_data=data.trend_data,
            avg_duration_ms=data.avg_duration_ms,
            pass_rate=data.pass_rate,
            create_user=user_info['id'],
        )
        result = await PityPhaseXReportDao.insert(model=model, log=True)

    return PityResponse.success(PityResponse.model_to_dict(result))

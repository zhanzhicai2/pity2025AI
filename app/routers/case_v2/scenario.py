"""
场景流程路由
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.handler.fatcory import PityResponse
from app.routers import Permission, get_session
from app.schema.scenario import (
    ScenarioSchema, ScenarioUpdateSchema,
    ScenarioStepSchema, ScenarioStepUpdateSchema
)
from app.models.scenario import PityScenario, PityScenarioStep
from app.crud.scenario import PityScenarioDao, PityScenarioStepDao

router = APIRouter(prefix='/case/v2/scenario', tags=['场景流程'])


# ============== 场景管理 ==============

@router.get('/list')
async def list_scenario(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        project_id: Optional[int] = None,
        case_type: Optional[str] = None,
        is_active: Optional[int] = None,
        user_info: dict = Depends(Permission()),
):
    """获取场景列表"""
    where = {}
    if project_id is not None:
        where["project_id"] = project_id
    if case_type:
        where["case_type"] = case_type
    if is_active is not None:
        where["is_active"] = is_active

    data, total = await PityScenarioDao.list_with_pagination(page, size, **where)
    return PityResponse.success_with_size(
        [PityResponse.model_to_dict(d) for d in data],
        total=total
    )


@router.get('')
async def get_scenario(id: int = Query(...)):
    """获取单个场景"""
    record = await PityScenarioDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='场景不存在')

    # 获取场景下的步骤
    from sqlalchemy import select
    from app.crud import async_session
    async with async_session() as session:
        stmt = select(PityScenarioStep).where(
            PityScenarioStep.scenario_id == id,
            PityScenarioStep.deleted_at == 0
        ).order_by(PityScenarioStep.step_order)
        result = await session.execute(stmt)
        steps = result.scalars().all()

    scenario_dict = PityResponse.model_to_dict(record)
    scenario_dict['steps'] = [PityResponse.model_to_dict(s) for s in steps]
    return PityResponse.success(scenario_dict)


@router.post('')
async def create_scenario(data: ScenarioSchema, user_info: dict = Depends(Permission())):
    """创建场景"""
    model = PityScenario(
        name=data.name,
        description=data.description,
        project_id=data.project_id,
        case_type=data.case_type,
        source=data.source,
        variables=data.variables,
        is_active=data.is_active,
        tags=data.tags,
        create_user=user_info['id'],
    )
    result = await PityScenarioDao.insert(model=model, log=True)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.put('')
async def update_scenario(data: ScenarioUpdateSchema, user_info: dict = Depends(Permission())):
    """更新场景"""
    update_data = {k: v for k, v in data.model_dump().items()
                   if v is not None and k != 'id'}
    if update_data:
        await PityScenarioDao.update_by_map(
            user_info['id'],
            PityScenario.id == data.id,
            **update_data
        )
    result = await PityScenarioDao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('')
async def delete_scenario(id: int = Query(...), user_info: dict = Depends(Permission()),
                          session=Depends(get_session)):
    """删除场景（同时删除关联步骤）"""
    # 先删除关联步骤
    from sqlalchemy import update
    await session.execute(
        update(PityScenarioStep).where(
            PityScenarioStep.scenario_id == id
        ).values(deleted_at=user_info['id'])
    )

    await PityScenarioDao.delete_record_by_id(session, user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


# ============== 场景步骤管理 ==============

@router.get('/step')
async def get_step(id: int = Query(...)):
    """获取单个步骤"""
    record = await PityScenarioStepDao.query_record(id=id)
    if not record:
        return PityResponse.failed(msg='步骤不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.post('/step')
async def create_step(data: ScenarioStepSchema, user_info: dict = Depends(Permission())):
    """创建步骤"""
    model = PityScenarioStep(
        scenario_id=data.scenario_id,
        case_id=data.case_id,
        step_order=data.step_order,
        step_name=data.step_name,
        input_mapping=data.input_mapping,
        output_mapping=data.output_mapping,
        condition=data.condition,
        condition_field=data.condition_field,
        timeout_ms=data.timeout_ms,
        retry_count=data.retry_count,
        retry_interval_ms=data.retry_interval_ms,
        create_user=user_info['id'],
    )
    result = await PityScenarioStepDao.insert(model=model, log=True)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.put('/step')
async def update_step(data: ScenarioStepUpdateSchema, user_info: dict = Depends(Permission())):
    """更新步骤"""
    update_data = {k: v for k, v in data.model_dump().items()
                   if v is not None and k != 'id'}
    if update_data:
        await PityScenarioStepDao.update_by_map(
            user_info['id'],
            PityScenarioStep.id == data.id,
            **update_data
        )
    result = await PityScenarioStepDao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('/step')
async def delete_step(id: int = Query(...), user_info: dict = Depends(Permission()),
                      session=Depends(get_session)):
    """删除步骤"""
    await PityScenarioStepDao.delete_record_by_id(session, user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


@router.get('/steps')
async def list_steps(
        scenario_id: int = Query(...),
        user_info: dict = Depends(Permission()),
):
    """获取场景的所有步骤"""
    from sqlalchemy import select
    from app.crud import async_session
    async with async_session() as session:
        stmt = select(PityScenarioStep).where(
            PityScenarioStep.scenario_id == scenario_id,
            PityScenarioStep.deleted_at == 0
        ).order_by(PityScenarioStep.step_order)
        result = await session.execute(stmt)
        steps = result.scalars().all()
    return PityResponse.success([PityResponse.model_to_dict(s) for s in steps])

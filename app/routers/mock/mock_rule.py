from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.crud.mock_rule.MockRuleDao import MockRuleDao
from app.exception.request import AuthException
from app.handler.fatcory import PityResponse
from app.models.mock_rule import MockRule
from app.routers import Permission
from app.schema.mock_rule import MockRuleSchema
from app.utils.logger import Log

router = APIRouter(prefix='/mock/rule', tags=['Mock规则管理'])
logger = Log('mock_rule')


@router.get('/list')
async def list_mock_rule(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        project_id: Optional[int] = None,
        name: Optional[str] = None,
        method: Optional[str] = None,
        is_active: Optional[bool] = None,
        user_info: dict = Depends(Permission()),
):
    """
    获取 Mock 规则列表（分页）
    """
    where = {"project_id": project_id, "method": method, "is_active": is_active}
    if name:
        where["name"] = f"%{name}%"
    data, total = await MockRuleDao.list_with_pagination(page, size, **where)
    # 转换 list 中的 model 对象为 dict
    return PityResponse.success_with_size([PityResponse.model_to_dict(d) for d in data], total=total)


@router.get('')
async def get_mock_rule(id: int = Query(...)):
    """
    获取单个 Mock 规则
    """
    record = await MockRuleDao.query_record(id=id)
    if not record:
        raise AuthException('记录不存在')
    return PityResponse.success(PityResponse.model_to_dict(record))


@router.post('')
async def create_mock_rule(data: MockRuleSchema, user_info: dict = Depends(Permission())):
    """
    创建 Mock 规则
    """
    model = MockRule(
        name=data.name,
        project_id=data.project_id,
        url_pattern=data.url_pattern,
        method=data.method,
        description=data.description,
        response_status=data.response_status,
        response_body=data.response_body,
        response_headers=data.response_headers,
        response_delay=data.response_delay,
        request_headers=data.request_headers,
        request_body_pattern=data.request_body_pattern,
        is_active=data.is_active,
        create_user=user_info['id'],
    )
    result = await MockRuleDao.insert(model=model, log=True)
    # insert 返回的 model 需要 expunge 后才能序列化
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.put('')
async def update_mock_rule(data: MockRuleSchema, user_info: dict = Depends(Permission())):
    """
    更新 Mock 规则
    """
    await MockRuleDao.update_by_map(
        user_info['id'],
        MockRule.id == data.id,
        name=data.name,
        project_id=data.project_id,
        url_pattern=data.url_pattern,
        method=data.method,
        description=data.description,
        response_status=data.response_status,
        response_body=data.response_body,
        response_headers=data.response_headers,
        response_delay=data.response_delay,
        request_headers=data.request_headers,
        request_body_pattern=data.request_body_pattern,
        is_active=data.is_active,
    )
    # 重新查询获取更新后的数据
    result = await MockRuleDao.query_record(id=data.id)
    return PityResponse.success(PityResponse.model_to_dict(result))


@router.delete('')
async def delete_mock_rule(id: int = Query(...), user_info: dict = Depends(Permission())):
    """
    删除 Mock 规则
    """
    await MockRuleDao.delete_record_by_id(user=user_info['id'], value=id)
    return PityResponse.success(msg='删除成功')


@router.patch('/toggle')
async def toggle_mock_rule(
        id: int = Query(...),
        is_active: bool = Query(...),
        user_info: dict = Depends(Permission()),
):
    """
    启用/禁用 Mock 规则
    """
    await MockRuleDao.update_by_map(user_info['id'], MockRule.id == id, is_active=is_active)
    return PityResponse.success(msg='更新成功')

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.crud.test_suite.TestSuiteDao import TestSuiteDao
from app.crud.test_suite.TestSuiteCaseDao import TestSuiteCaseDao
from app.crud.test_suite.TestSuiteVariableDao import TestSuiteVariableDao
from app.crud.test_suite.TestSuiteExecutionDao import TestSuiteExecutionDao
from app.handler.fatcory import PityResponse
from app.routers import Permission
from app.schema.test_suite import (
    TestSuiteCreate,
    TestSuiteResponse,
    TestSuiteUpdate,
    TestSuiteCaseCreate,
    TestSuiteCaseUpdate,
    TestSuiteCaseResponse,
    TestSuiteCaseReorderRequest,
    TestSuiteVariableCreate,
    TestSuiteVariableUpdate,
    TestSuiteVariableResponse,
    TestSuiteRunRequest,
    TestSuiteRunResponse,
)

router = APIRouter(prefix="/suite", tags=["测试套件"])


# ==================== TestSuite ====================

@router.get("/")
async def list_suite(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = None,
):
    """获取测试套件列表"""
    kwargs = {}
    if project_id is not None:
        kwargs["project_id"] = project_id
    data, total = await TestSuiteDao.list_suite(page, size, **kwargs)
    return PityResponse.success(data={"list": data, "total": total})


@router.post("/", response_model=TestSuiteResponse)
async def create_suite(
    form: TestSuiteCreate,
    user_info: dict = Depends(Permission()),
):
    """创建测试套件"""
    user_id = user_info.get("id")
    suite = await TestSuiteDao.insert_suite(form, user_id)
    return PityResponse.success(suite)


@router.get("/{suite_id}", response_model=TestSuiteResponse)
async def get_suite(suite_id: int):
    """获取测试套件详情"""
    suite = await TestSuiteDao.query_suite(suite_id)
    if suite is None:
        return PityResponse.failed(msg="套件不存在")
    return PityResponse.success(suite)


@router.put("/{suite_id}", response_model=TestSuiteResponse)
async def update_suite(
    suite_id: int,
    form: TestSuiteUpdate,
    user_info: dict = Depends(Permission()),
):
    """更新测试套件"""
    user_id = user_info.get("id")
    suite = await TestSuiteDao.update_suite(suite_id, form, user_id)
    return PityResponse.success(suite)


@router.delete("/{suite_id}")
async def delete_suite(
    suite_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除测试套件"""
    user_id = user_info.get("id")
    await TestSuiteDao.delete_suite(suite_id, user_id)
    return PityResponse.success(msg="删除成功")


# ==================== TestSuiteCase ====================

@router.get("/{suite_id}/cases")
async def list_suite_cases(
    suite_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
):
    """获取套件用例列表"""
    data, total = await TestSuiteCaseDao.list_cases(page, size, suite_id)
    return PityResponse.success(data={"list": data, "total": total})


@router.post("/{suite_id}/case", response_model=TestSuiteCaseResponse)
async def add_case_to_suite(
    suite_id: int,
    form: TestSuiteCaseCreate,
    user_info: dict = Depends(Permission()),
):
    """添加用例到套件"""
    user_id = user_info.get("id")
    suite_case = await TestSuiteCaseDao.insert_case(form, suite_id, user_id)
    return PityResponse.success(suite_case)


@router.put("/{suite_id}/case/{case_id}", response_model=TestSuiteCaseResponse)
async def update_suite_case(
    suite_id: int,
    case_id: int,
    form: TestSuiteCaseUpdate,
    user_info: dict = Depends(Permission()),
):
    """更新套件用例"""
    user_id = user_info.get("id")
    suite_case = await TestSuiteCaseDao.update_case(case_id, form, user_id)
    return PityResponse.success(suite_case)


@router.delete("/{suite_id}/case/{case_id}")
async def remove_case_from_suite(
    suite_id: int,
    case_id: int,
    user_info: dict = Depends(Permission()),
):
    """从套件移除用例"""
    user_id = user_info.get("id")
    await TestSuiteCaseDao.delete_case(case_id, user_id)
    return PityResponse.success(msg="移除成功")


@router.put("/{suite_id}/cases/reorder")
async def reorder_cases(
    suite_id: int,
    form: TestSuiteCaseReorderRequest,
    user_info: dict = Depends(Permission()),
):
    """批量排序用例"""
    user_id = user_info.get("id")
    await TestSuiteCaseDao.reorder_cases(suite_id, form.cases, user_id)
    return PityResponse.success(msg="排序成功")


# ==================== TestSuiteVariable ====================

@router.get("/{suite_id}/variables")
async def list_suite_variables(suite_id: int):
    """获取套件变量列表"""
    data = await TestSuiteVariableDao.list_variables(suite_id)
    return PityResponse.success(data=data)


@router.post("/{suite_id}/variable", response_model=TestSuiteVariableResponse)
async def create_variable(
    suite_id: int,
    form: TestSuiteVariableCreate,
    user_info: dict = Depends(Permission()),
):
    """添加套件变量"""
    user_id = user_info.get("id")
    variable = await TestSuiteVariableDao.insert_variable(form, suite_id, user_id)
    return PityResponse.success(variable)


@router.put("/{suite_id}/variable/{var_id}", response_model=TestSuiteVariableResponse)
async def update_variable(
    suite_id: int,
    var_id: int,
    form: TestSuiteVariableUpdate,
    user_info: dict = Depends(Permission()),
):
    """更新套件变量"""
    user_id = user_info.get("id")
    variable = await TestSuiteVariableDao.update_variable(var_id, form, user_id)
    return PityResponse.success(variable)


@router.delete("/{suite_id}/variable/{var_id}")
async def delete_variable(
    suite_id: int,
    var_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除套件变量"""
    user_id = user_info.get("id")
    await TestSuiteVariableDao.delete_variable(var_id, user_id)
    return PityResponse.success(msg="删除成功")


# ==================== TestSuiteExecution ====================

@router.get("/{suite_id}/executions")
async def list_suite_executions(
    suite_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """获取套件执行历史"""
    data, total = await TestSuiteExecutionDao.list_executions(page, size, suite_id)
    return PityResponse.success(data={"list": data, "total": total})


@router.post("/{suite_id}/run", response_model=TestSuiteRunResponse)
async def run_suite(
    suite_id: int,
    form: TestSuiteRunRequest,
    user_info: dict = Depends(Permission()),
):
    """立即执行测试套件"""
    suite = await TestSuiteDao.query_suite(suite_id)
    if suite is None:
        return PityResponse.failed(msg="套件不存在")

    user_id = user_info.get("id")
    trace_id = str(uuid.uuid4())

    # 创建执行记录
    execution = await TestSuiteExecutionDao.insert_execution(
        suite_id=suite_id,
        trace_id=trace_id,
        executor=form.executor or user_id,
        user_id=user_id,
    )

    # 在后台执行套件
    from app.utils.suite_executor import SuiteExecutor
    SuiteExecutor.run(suite_id, execution.id, form.params or {})

    return PityResponse.success(TestSuiteRunResponse(
        execution_id=execution.id,
        trace_id=trace_id,
        status="pending",
        message="套件执行已提交",
    ))

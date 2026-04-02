import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.crud.scheduler.CrontabScheduleDao import PityCrontabScheduleDao
from app.crud.scheduler.IntervalScheduleDao import PityIntervalScheduleDao
from app.crud.scheduler.PeriodicTaskDao import PityPeriodicTaskDao
from app.crud.scheduler.TaskExecutionDao import PityTaskExecutionDao
from app.handler.fatcory import PityResponse
from app.routers import Permission
from app.schema.scheduler import (
    CrontabScheduleCreate,
    CrontabScheduleResponse,
    IntervalScheduleCreate,
    IntervalScheduleResponse,
    PeriodicTaskCreate,
    PeriodicTaskResponse,
    PeriodicTaskUpdate,
    TaskExecutionResponse,
    TaskRunRequest,
    TaskRunResponse,
)
from app.utils.scheduler import Scheduler

router = APIRouter(prefix="/scheduler", tags=["调度任务"])


# ==================== Crontab Schedule ====================

@router.get("/crontab/")
async def list_crontab(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """获取 Crontab 调度列表"""
    data, total = await PityCrontabScheduleDao.list_crontab(page=page, size=size)
    return PityResponse.success(data={"list": data, "total": total})


@router.post("/crontab/", response_model=CrontabScheduleResponse)
async def create_crontab(
    form: CrontabScheduleCreate,
    user_info: dict = Depends(Permission()),
):
    """创建 Crontab 调度"""
    user_id = user_info.get("id")
    crontab = await PityCrontabScheduleDao.insert_crontab(form, user_id)
    return PityResponse.success(crontab)


@router.delete("/crontab/{crontab_id}")
async def delete_crontab(
    crontab_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除 Crontab 调度"""
    user_id = user_info.get("id")
    await PityCrontabScheduleDao.delete_crontab(crontab_id, user_id)
    return PityResponse.success(msg="删除成功")


# ==================== Interval Schedule ====================

@router.get("/interval/")
async def list_interval(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """获取 Interval 调度列表"""
    data, total = await PityIntervalScheduleDao.list_interval(page=page, size=size)
    return PityResponse.success(data={"list": data, "total": total})


@router.post("/interval/", response_model=IntervalScheduleResponse)
async def create_interval(
    form: IntervalScheduleCreate,
    user_info: dict = Depends(Permission()),
):
    """创建 Interval 调度"""
    user_id = user_info.get("id")
    interval = await PityIntervalScheduleDao.insert_interval(form, user_id)
    return PityResponse.success(interval)


@router.delete("/interval/{interval_id}")
async def delete_interval(
    interval_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除 Interval 调度"""
    user_id = user_info.get("id")
    await PityIntervalScheduleDao.delete_interval(interval_id, user_id)
    return PityResponse.success(msg="删除成功")


# ==================== Periodic Task ====================

@router.get("/task/")
async def list_task(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = None,
    task_type: Optional[str] = None,
    enabled: Optional[bool] = None,
):
    """获取周期任务列表"""
    kwargs = {}
    if project_id is not None:
        kwargs["project_id"] = project_id
    if task_type is not None:
        kwargs["task_type"] = task_type
    if enabled is not None:
        kwargs["enabled"] = enabled

    data, total = await PityPeriodicTaskDao.list_task(page, size, **kwargs)

    # 获取调度器中的任务状态
    result = Scheduler.list_periodic_tasks(data)
    return PityResponse.success(data={"list": result, "total": total})


@router.post("/task/", response_model=PeriodicTaskResponse)
async def create_task(
    form: PeriodicTaskCreate,
    user_info: dict = Depends(Permission()),
):
    """创建周期任务"""
    user_id = user_info.get("id")
    # 如果使用 crontab 调度，先创建 crontab 记录
    if form.schedule_type == "crontab" and form.crontab_data:
        crontab = await PityCrontabScheduleDao.insert_crontab(form.crontab_data, user_id)
        form.crontab_id = crontab.id

    # 如果使用 interval 调度，先创建 interval 记录
    if form.schedule_type == "interval" and form.interval_data:
        interval = await PityIntervalScheduleDao.insert_interval(form.interval_data, user_id)
        form.interval_id = interval.id

    # 创建任务
    task = await PityPeriodicTaskDao.insert_task(form, user_id)

    # 添加到调度器
    Scheduler.add_periodic_task(task.id, task.name, task)

    return PityResponse.success(task)


@router.get("/task/{task_id}", response_model=PeriodicTaskResponse)
async def get_task(task_id: int):
    """获取任务详情"""
    task = await PityPeriodicTaskDao.query_task(task_id)
    if task is None:
        return PityResponse.failed(msg="任务不存在")
    return PityResponse.success(task)


@router.put("/task/{task_id}", response_model=PeriodicTaskResponse)
async def update_task(
    task_id: int,
    form: PeriodicTaskUpdate,
    user_info: dict = Depends(Permission()),
):
    """更新任务"""
    user_id = user_info.get("id")
    task = await PityPeriodicTaskDao.update_task(task_id, form, user_id)

    # 同步更新调度器中的任务
    Scheduler.update_periodic_task(task.id, task.name, task)

    return PityResponse.success(task)


@router.delete("/task/{task_id}")
async def delete_task(
    task_id: int,
    user_info: dict = Depends(Permission()),
):
    """删除任务"""
    user_id = user_info.get("id")
    await PityPeriodicTaskDao.delete_task(task_id, user_id)

    # 从调度器移除
    Scheduler.remove_periodic_task(task_id)

    return PityResponse.success(msg="删除成功")


@router.put("/task/{task_id}/toggle")
async def toggle_task(
    task_id: int,
    user_info: dict = Depends(Permission()),
):
    """启用/禁用任务"""
    task = await PityPeriodicTaskDao.query_task(task_id)
    if task is None:
        return PityResponse.failed(msg="任务不存在")

    new_status = not task.enabled
    user_id = user_info.get("id")
    await PityPeriodicTaskDao.toggle_task(task_id, new_status, user_id)

    # 同步调度器
    Scheduler.toggle_periodic_task(task_id, new_status)

    return PityResponse.success(msg=f"任务已{'启用' if new_status else '禁用'}")


# ==================== Task Execution ====================

@router.get("/task/{task_id}/executions")
async def list_task_executions(
    task_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """获取任务执行记录"""
    data, total = await PityTaskExecutionDao.list_executions_by_task(task_id, page, size)
    return PityResponse.success(data={"list": data, "total": total})


@router.post("/task/{task_id}/run", response_model=TaskRunResponse)
async def run_task_now(
    task_id: int,
    form: TaskRunRequest,
    user_info: dict = Depends(Permission()),
):
    """立即执行任务"""
    task = await PityPeriodicTaskDao.query_task(task_id)
    if task is None:
        return PityResponse.failed(msg="任务不存在")

    user_id = user_info.get("id")
    trace_id = str(uuid.uuid4())

    # 创建执行记录
    execution = await PityTaskExecutionDao.insert_execution(
        task_id=task_id,
        trace_id=trace_id,
        executor=form.executor or user_id,
        user_id=user_id,
    )

    # 在后台执行任务
    await Scheduler.run_task_now(task_id, trace_id, execution.id, form.params or {})

    return PityResponse.success(TaskRunResponse(
        execution_id=execution.id,
        trace_id=trace_id,
        status="pending",
        message="任务已提交执行",
    ))


@router.get("/execution/{execution_id}", response_model=TaskExecutionResponse)
async def get_execution(execution_id: int):
    """获取执行记录详情"""
    execution = await PityTaskExecutionDao.query_execution(execution_id)
    if execution is None:
        return PityResponse.failed(msg="执行记录不存在")
    return PityResponse.success(execution)

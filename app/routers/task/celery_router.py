"""
Celery 异步任务路由

提供任务状态查询接口
"""
from fastapi import APIRouter, Depends

from app.handler.fatcory import PityResponse
from app.routers import Permission
from app.schema.celery_task import TaskStatusResponse

router = APIRouter(prefix="/task", tags=["异步任务"])


@router.get("/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    user_info: dict = Depends(Permission()),
):
    """
    查询任务状态

    Args:
        task_id: Celery 任务 ID

    Returns:
        任务状态信息
    """
    from celery_app import celery_app

    # 获取任务状态
    task = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": task.state,
    }

    # 根据状态添加更多信息
    if task.state == "PENDING":
        response["message"] = "任务等待中..."
    elif task.state == "STARTED":
        response["message"] = "任务执行中..."
    elif task.state == "SUCCESS":
        result = task.result
        response["result"] = result
        response["message"] = "任务完成"
    elif task.state == "FAILURE":
        response["error"] = str(task.info)
        response["message"] = "任务失败"
    elif task.state == "RETRY":
        response["message"] = "任务重试中..."
    elif task.state == "REVOKED":
        response["message"] = "任务已取消"

    return PityResponse.success(response)


@router.get("/{task_id}/result", response_model=dict)
async def get_task_result(
    task_id: str,
    user_info: dict = Depends(Permission()),
):
    """
    获取任务结果

    仅在任务成功时返回结果
    """
    from celery_app import celery_app

    task = celery_app.AsyncResult(task_id)

    if task.state == "SUCCESS":
        return PityResponse.success(task.result)
    elif task.state == "FAILURE":
        return PityResponse.failed(msg=f"任务失败: {task.info}")
    else:
        return PityResponse.failed(msg=f"任务未完成，当前状态: {task.state}")

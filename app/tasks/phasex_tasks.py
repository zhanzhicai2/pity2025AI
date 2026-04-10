"""
Phase X 异步任务

使用 Celery 处理 Phase X 测试计划的定时和异步执行
"""
import asyncio
import json
from typing import Any, Dict

from celery import Task
from celery_app import celery_app
from loguru import logger


class PhaseXCallbackTask(Task):
    """Phase X 任务回调基类"""

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        logger.bind(name="celery").info(f"PhaseX Task {task_id} succeeded: {retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.bind(name="celery").error(f"PhaseX Task {task_id} failed: {exc}")
        # 更新执行记录状态为失败
        try:
            execution_id = kwargs.get('execution_id')
            if execution_id:
                run_async(self._update_execution_status(execution_id, 'error', str(exc)))
        except Exception as e:
            logger.bind(name="celery").error(f"更新执行记录失败: {e}")


def run_async(coro):
    """在 Celery worker 中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


async def _update_execution_status(execution_id: int, status: str, error_message: str = None):
    """更新执行记录状态"""
    from app.crud.phasex import PityPhaseXExecutionDao
    from app.models.phasex import PityPhaseXExecution

    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message

    # 需要获取一个 user_id，这里使用系统用户
    await PityPhaseXExecutionDao.update_by_map(
        1,  # 系统用户
        PityPhaseXExecution.id == execution_id,
        **update_data
    )


async def _create_execution_record(plan_id: int, project_id: int, user_id: int) -> int:
    """创建执行记录，返回执行记录ID"""
    from app.crud.phasex import PityPhaseXExecutionDao
    from app.models.phasex import PityPhaseXExecution

    model = PityPhaseXExecution(
        plan_id=plan_id,
        project_id=project_id,
        status='running',
        executor=f'user_{user_id}',
        create_user=user_id,
    )
    result = await PityPhaseXExecutionDao.insert(model=model, log=True)
    return result.id


@celery_app.task(bind=True, base=PhaseXCallbackTask, name='phasex.execute_plan')
def execute_plan(self, plan_id: int, user_id: int, execution_id: int = None):
    """
    执行 Phase X 测试计划

    Args:
        plan_id: 计划ID
        user_id: 用户ID
        execution_id: 执行记录ID（可选）
    """
    logger.bind(name="celery").info(f"开始执行 PhaseX Plan: {plan_id}")

    # 如果没有传入 execution_id，创建一个
    if not execution_id:
        execution_id = run_async(_create_execution_record(plan_id, 1, user_id))

    try:
        # 获取计划信息
        from app.crud.phasex import PityPhaseXPlanDao
        plan = run_async(PityPhaseXPlanDao.query_record(id=plan_id))

        if not plan:
            return {"status": "error", "message": f"计划不存在: {plan_id}"}

        # 根据 plan_type 分发执行
        if plan.plan_type == "scenario":
            result = run_async(_execute_scenario(plan, execution_id, user_id))
        elif plan.plan_type == "single":
            result = run_async(_execute_single_case(plan, execution_id, user_id))
        elif plan.plan_type == "suite":
            result = run_async(_execute_suite(plan, execution_id, user_id))
        else:
            result = {"status": "error", "message": f"不支持的执行类型: {plan.plan_type}"}

        # 更新执行记录
        run_async(_update_execution_result(execution_id, result))

        # 更新计划的上次执行ID
        run_async(_update_plan_last_execution(plan_id, execution_id))

        return result

    except Exception as e:
        logger.bind(name="celery").error(f"执行 PhaseX Plan 失败: {e}")
        run_async(_update_execution_status(execution_id, 'error', str(e)))
        raise


async def _execute_scenario(plan, execution_id: int, user_id: int) -> Dict[str, Any]:
    """执行场景流程"""
    from app.core.scenario_executor import ScenarioExecutor

    executor = ScenarioExecutor(user_id=user_id)
    result = await executor.execute_scenario(
        scenario_id=plan.target_id,
        environment_id=plan.environment_id
    )

    return result


async def _execute_single_case(plan, execution_id: int, user_id: int) -> Dict[str, Any]:
    """执行单个用例"""
    from app.core.scenario_executor import CaseV2Executor

    executor = CaseV2Executor(user_id=user_id)
    result = await executor.execute_case(
        case_id=plan.target_id,
        environment_id=plan.environment_id
    )

    return result


async def _execute_suite(plan, execution_id: int, user_id: int) -> Dict[str, Any]:
    """执行测试套件"""
    # TODO: 对接现有的 test_suite 执行逻辑
    return {
        "status": "error",
        "message": "测试套件执行暂未实现"
    }


async def _update_execution_result(execution_id: int, result: Dict[str, Any]):
    """更新执行记录结果"""
    from app.crud.phasex import PityPhaseXExecutionDao
    from app.models.phasex import PityPhaseXExecution

    duration_ms = result.get("duration_ms")
    status = result.get("status", "error")

    update_data = {
        "status": status,
        "duration_ms": duration_ms,
        "response_data": json.dumps(result, ensure_ascii=False),
    }

    if status == "error":
        update_data["error_message"] = result.get("error", "")

    if "step_results" in result:
        update_data["step_results"] = json.dumps(result["step_results"], ensure_ascii=False)

    await PityPhaseXExecutionDao.update_by_map(
        1,
        PityPhaseXExecution.id == execution_id,
        **update_data
    )


async def _update_plan_last_execution(plan_id: int, execution_id: int):
    """更新计划的上次执行ID"""
    from app.crud.phasex import PityPhaseXPlanDao
    from app.models.phasex import PityPhaseXPlan

    await PityPhaseXPlanDao.update_by_map(
        1,
        PityPhaseXPlan.id == plan_id,
        last_execution_id=execution_id
    )


@celery_app.task(bind=True, base=PhaseXCallbackTask, name='phasex.execute_ai_generation')
def execute_ai_generation(self, task_id: int, user_id: int):
    """
    执行 AI 用例生成任务

    Args:
        task_id: AI 生成任务ID
        user_id: 用户ID
    """
    logger.bind(name="celery").info(f"开始执行 AI 生成任务: {task_id}")

    try:
        from app.core.ai.case_generator import AIGenerationWorkflow

        workflow = AIGenerationWorkflow(user_id=user_id)
        result = run_async(workflow.execute(task_id))

        return result

    except Exception as e:
        logger.bind(name="celery").error(f"执行 AI 生成任务失败: {e}")
        raise


# Celery Beat 定时任务调度
from celery.schedules import crontab

# 配置定时任务
celery_app.conf.beat_schedule = {
    # 示例：每天凌晨执行一次测试计划
    # 'phasex-daily-run': {
    #     'task': 'phasex.execute_plan',
    #     'schedule': crontab(hour=0, minute=0),
    #     'args': (plan_id, user_id),
    # },
}

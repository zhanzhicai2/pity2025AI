import asyncio
from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.executor import Executor
from app.handler.fatcory import PityResponse


class Scheduler(object):
    scheduler: AsyncIOScheduler = None

    @staticmethod
    def init(scheduler):
        Scheduler.scheduler = scheduler

    @staticmethod
    def configure(**kwargs):
        Scheduler.scheduler.configure(**kwargs)

    @staticmethod
    def start():
        Scheduler.scheduler.start()

    @staticmethod
    def add_test_plan(plan_id, plan_name, cron):
        return Scheduler.scheduler.add_job(func=Executor.run_test_plan, args=(plan_id,),
                                           name=plan_name, id=str(plan_id),
                                           trigger=CronTrigger.from_crontab(cron))

    @staticmethod
    def edit_test_plan(plan_id, plan_name, cron):
        """
        通过测试计划id，更新测试计划任务的cron，name等数据
        :param plan_id:
        :param plan_name:
        :param cron:
        :return:
        """
        job = Scheduler.scheduler.get_job(str(plan_id))
        if job is None:
            # 新增job
            return Scheduler.add_test_plan(plan_id, plan_name, cron)
        Scheduler.scheduler.modify_job(job_id=str(plan_id), trigger=CronTrigger.from_crontab(cron), name=plan_name)
        Scheduler.scheduler.pause_job(str(plan_id))
        Scheduler.scheduler.resume_job(str(plan_id))

    @staticmethod
    def pause_resume_test_plan(plan_id, status):
        """
        暂停或恢复测试计划，会影响到next_run_at
        :param plan_id:
        :param status:
        :return:
        """
        if status:
            Scheduler.scheduler.resume_job(job_id=str(plan_id))
        else:
            Scheduler.scheduler.pause_job(str(plan_id))

    @staticmethod
    def remove(plan_id):
        """
        删除job，当删除测试计划时，调用此方法
        :param plan_id:
        :return:
        """
        Scheduler.scheduler.remove_job(str(plan_id))

    @staticmethod
    def list_test_plan(data: List):
        ans = []
        for d, follow in data:
            temp = PityResponse.model_to_dict(d)
            temp['follow'] = follow is not None
            job = Scheduler.scheduler.get_job(str(temp.get('id')))
            if job is None:
                # 说明job初始化失败了
                temp["state"] = 2
                ans.append(temp)
                continue
            if job.next_run_time is None:
                # 说明job被暂停了
                temp["state"] = 3
            else:
                temp["next_run"] = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            ans.append(temp)
        return ans

    # ==================== Periodic Task Management ====================

    @staticmethod
    async def _execute_periodic_task(task_id: int, execution_id: int):
        """执行周期任务的内部方法"""
        from app.crud.scheduler.TaskExecutionDao import PityTaskExecutionDao
        from app.crud.scheduler.PeriodicTaskDao import PityPeriodicTaskDao

        try:
            # 更新执行状态为 running
            await PityTaskExecutionDao.update_execution_running(execution_id)

            # 获取任务配置
            task = await PityPeriodicTaskDao.query_task(task_id)
            if task is None:
                await PityTaskExecutionDao.update_execution_failed(
                    execution_id, "任务不存在", user_id=0
                )
                return

            task_config = task.task_config or {}

            # 根据任务类型执行
            if task.task_type == "test_plan":
                plan_id = task_config.get("plan_id")
                if plan_id:
                    await Executor.run_test_plan(plan_id)
                    result = {"plan_id": plan_id, "executed": True}
                else:
                    result = {"error": "plan_id not found in task_config"}

            elif task.task_type == "testcase":
                case_id = task_config.get("case_id")
                env_id = task_config.get("env_id")
                if case_id and env_id:
                    # 执行单个测试用例
                    executor = Executor()
                    result, error = await executor.run(env_id, case_id)
                    if error:
                        await PityTaskExecutionDao.update_execution_failed(
                            execution_id, error, user_id=0
                        )
                        return
                    await PityTaskExecutionDao.update_execution_success(
                        execution_id, result, user_id=0
                    )
                    return
                result = {"error": "case_id or env_id not found in task_config"}

            elif task.task_type == "http":
                # HTTP 请求任务
                result = {"type": "http", "status": "not_implemented"}

            elif task.task_type == "sql":
                # SQL 执行任务
                result = {"type": "sql", "status": "not_implemented"}

            elif task.task_type == "redis":
                # Redis 操作任务
                result = {"type": "redis", "status": "not_implemented"}

            elif task.task_type == "python":
                # Python 脚本任务
                result = {"type": "python", "status": "not_implemented"}

            else:
                result = {"error": f"unknown task_type: {task.task_type}"}

            await PityTaskExecutionDao.update_execution_success(
                execution_id, result, user_id=0
            )

        except Exception as e:
            try:
                from app.crud.scheduler.TaskExecutionDao import PityTaskExecutionDao
                await PityTaskExecutionDao.update_execution_failed(
                    execution_id, str(e), user_id=0
                )
            except Exception:
                pass

    @staticmethod
    async def run_task_now(task_id: int, trace_id: str, execution_id: int, params: dict):
        """立即执行任务"""
        asyncio.create_task(Scheduler._execute_periodic_task(task_id, execution_id))

    @staticmethod
    async def _get_trigger(task_record):
        """获取任务触发器"""
        if task_record.schedule_type == "crontab":
            from app.crud.scheduler.CrontabScheduleDao import PityCrontabScheduleDao
            crontab = await PityCrontabScheduleDao.query_crontab(task_record.crontab_id)
            if crontab:
                return CronTrigger(
                    minute=crontab.minute,
                    hour=crontab.hour,
                    day_of_week=crontab.day_of_week,
                    day=crontab.day_of_month,
                    month=crontab.month_of_year,
                )
        elif task_record.schedule_type == "interval":
            from app.crud.scheduler.IntervalScheduleDao import PityIntervalScheduleDao
            interval = await PityIntervalScheduleDao.query_interval(task_record.interval_id)
            if interval:
                return IntervalTrigger(
                    **{interval.interval_type: interval.interval_value}
                )
        return None

    @staticmethod
    async def add_periodic_task_async(task_id: int, name: str, task_record):
        """异步添加周期任务到调度器"""
        try:
            job_id = f"periodic_task_{task_id}"
            trigger = await Scheduler._get_trigger(task_record)
            if trigger is None:
                return None

            return Scheduler.scheduler.add_job(
                func=Scheduler._execute_periodic_task,
                args=(task_id, None),
                name=name,
                id=job_id,
                trigger=trigger,
                replace_existing=True,
            )
        except Exception as e:
            print(f"Failed to add periodic task: {e}")
            return None

    @staticmethod
    def add_periodic_task(task_id: int, name: str, task_record):
        """添加周期任务到调度器（同步包装）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在运行中，使用 ensure_future
                asyncio.ensure_future(
                    Scheduler.add_periodic_task_async(task_id, name, task_record)
                )
            else:
                loop.run_until_complete(
                    Scheduler.add_periodic_task_async(task_id, name, task_record)
                )
        except Exception as e:
            print(f"Failed to add periodic task: {e}")

    @staticmethod
    def update_periodic_task(task_id: int, name: str, task_record):
        """更新周期任务"""
        job_id = f"periodic_task_{task_id}"
        # 先移除旧任务
        try:
            Scheduler.scheduler.remove_job(job_id)
        except Exception:
            pass
        # 重新添加
        if task_record.enabled:
            Scheduler.add_periodic_task(task_id, name, task_record)

    @staticmethod
    def remove_periodic_task(task_id: int):
        """移除周期任务"""
        job_id = f"periodic_task_{task_id}"
        try:
            Scheduler.scheduler.remove_job(job_id)
        except Exception:
            pass

    @staticmethod
    def toggle_periodic_task(task_id: int, enabled: bool):
        """启用/禁用周期任务"""
        job_id = f"periodic_task_{task_id}"
        try:
            if enabled:
                Scheduler.scheduler.resume_job(job_id)
            else:
                Scheduler.scheduler.pause_job(job_id)
        except Exception:
            pass

    @staticmethod
    def list_periodic_tasks(data: List):
        """获取周期任务列表及状态"""
        ans = []
        for d in data:
            temp = PityResponse.model_to_dict(d)
            job_id = f"periodic_task_{temp.get('id')}"
            job = Scheduler.scheduler.get_job(job_id)
            if job is None:
                temp["state"] = 2  # 未调度
                temp["next_run_time"] = None
            elif job.next_run_time is None:
                temp["state"] = 3  # 暂停
                temp["next_run_time"] = None
            else:
                temp["state"] = 1  # 正常运行
                temp["next_run_time"] = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            ans.append(temp)
        return ans

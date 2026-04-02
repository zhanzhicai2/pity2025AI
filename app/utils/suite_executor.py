import asyncio
import time
from datetime import datetime
from typing import List

from loguru import logger

from app.core.executor import Executor
from app.crud.test_suite.TestSuiteCaseDao import TestSuiteCaseDao
from app.crud.test_suite.TestSuiteDao import TestSuiteDao
from app.crud.test_suite.TestSuiteExecutionDao import TestSuiteExecutionDao
from app.crud.test_suite.TestSuiteVariableDao import TestSuiteVariableDao


class SuiteExecutor:
    """
    测试套件执行器
    在后台线程中执行测试套件，遍历套件中的用例并执行
    """

    @staticmethod
    async def run(suite_id: int, execution_id: int, params: dict):
        """
        执行测试套件

        Args:
            suite_id: 套件 ID
            execution_id: 执行记录 ID
            params: 执行参数（运行时变量）
        """
        # 在后台线程中运行，不阻塞主事件循环
        asyncio.create_task(SuiteExecutor._execute(suite_id, execution_id, params))

    @staticmethod
    async def _execute(suite_id: int, execution_id: int, params: dict):
        """实际执行逻辑"""
        user_id = 0  # 系统执行
        start_time = datetime.now()

        try:
            # 更新状态为 running
            await TestSuiteExecutionDao.update_execution_started(execution_id)

            # 获取套件信息
            suite = await TestSuiteDao.query_suite(suite_id)
            if suite is None:
                await TestSuiteExecutionDao.update_execution_failed(
                    execution_id, "套件不存在", user_id
                )
                return

            # 获取所有启用的用例（按顺序）
            suite_cases = await TestSuiteCaseDao.list_all_cases(suite_id)
            if not suite_cases:
                await TestSuiteExecutionDao.update_execution_result(
                    execution_id, 0, 0, 0, 0, user_id
                )
                return

            # 加载套件变量
            suite_vars = await TestSuiteVariableDao.list_variables(suite_id)
            for var in suite_vars:
                params[var.key] = SuiteExecutor._parse_variable(var.value, var.var_type)

            total = len(suite_cases)
            passed, failed, error = 0, 0, 0

            # 执行模式：sequential（顺序）或 parallel（并行）
            if suite.execution_mode == "parallel":
                results = await SuiteExecutor._run_parallel(
                    suite.env_id, suite_cases, params, suite.retry_on_failure, suite.stop_on_failure
                )
            else:
                results = await SuiteExecutor._run_sequential(
                    suite.env_id, suite_cases, params, suite.retry_on_failure, suite.stop_on_failure
                )

            for status in results:
                if status == 0:
                    passed += 1
                elif status == 1:
                    failed += 1
                else:
                    error += 1

            # 更新执行结果
            await TestSuiteExecutionDao.update_execution_result(
                execution_id, total, passed, failed, error, user_id
            )

        except Exception as e:
            logger.exception(f"套件执行异常: suite_id={suite_id}, execution_id={execution_id}")
            await TestSuiteExecutionDao.update_execution_failed(execution_id, str(e), user_id)

    @staticmethod
    async def _run_sequential(
        env_id: int,
        suite_cases: List,
        params: dict,
        retry_on_failure: bool,
        stop_on_failure: bool,
    ) -> List[int]:
        """顺序执行用例"""
        results = []
        for suite_case in suite_cases:
            status = await SuiteExecutor._run_single_case(
                env_id, suite_case, params, retry_on_failure
            )
            results.append(status)

            # 如果失败且设置了 stop_on_failure，停止后续执行
            if status != 0 and stop_on_failure:
                logger.bind(name=None).info(
                    f"用例 {suite_case.case_id} 失败，停止后续执行"
                )
                # 剩余用例标记为跳过
                remaining = len(suite_cases) - len(results)
                results.extend([3] * remaining)  # 3 = skip
                break

        return results

    @staticmethod
    async def _run_parallel(
        env_id: int,
        suite_cases: List,
        params: dict,
        retry_on_failure: bool,
        stop_on_failure: bool,
    ) -> List[int]:
        """并行执行用例"""
        tasks = [
            SuiteExecutor._run_single_case(env_id, suite_case, params, retry_on_failure)
            for suite_case in suite_cases
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.bind(name=None).error(
                    f"用例 {suite_cases[i].case_id} 执行异常: {result}"
                )
                final_results.append(2)  # error
            else:
                final_results.append(result)

        return final_results

    @staticmethod
    async def _run_single_case(
        env_id: int, suite_case, params: dict, retry_on_failure: bool
    ) -> int:
        """
        执行单个用例

        Returns:
            0 = 通过, 1 = 失败, 2 = 错误
        """
        retry_times = suite_case.retry if retry_on_failure else 0
        case_params = params.copy()

        for attempt in range(retry_times + 1):
            try:
                # 复用 Executor 执行单个用例
                executor = Executor()
                result, err = await executor.run(
                    env=env_id,
                    case_id=suite_case.case_id,
                    params_pool=case_params,
                    request_param={},
                    path=f"套件用例[{suite_case.case_id}]",
                )

                if err is not None:
                    # 执行出错
                    if attempt < retry_times:
                        await asyncio.sleep(1)  # 重试间隔
                        continue
                    return 2  # error

                # 检查断言结果
                if result.get("status"):
                    return 0  # passed
                else:
                    if attempt < retry_times:
                        await asyncio.sleep(1)
                        continue
                    return 1  # failed

            except Exception as e:
                logger.bind(name=None).exception(
                    f"执行用例 {suite_case.case_id} 失败: {e}"
                )
                if attempt < retry_times:
                    await asyncio.sleep(1)
                    continue
                return 2  # error

        return 1  # 默认返回失败

    @staticmethod
    def _parse_variable(value: str, var_type: str):
        """解析变量值"""
        import json

        if var_type == "json":
            try:
                return json.loads(value)
            except:
                return value
        elif var_type == "yaml":
            # 简单的 YAML 解析（可扩展）
            return value
        else:
            return value

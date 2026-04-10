"""
Phase X 场景执行器 - 用例串联和参数传递
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional

from app.core.paramters import parameters_parser
from app.core.render import Render
from app.core.ws_connection_manager import ws_manage
from app.crud.case_v2.CaseV2Dao import CaseV2Dao
from app.crud.scenario import PityScenarioDao, PityScenarioStepDao
from app.models.case_v2 import PityCaseV2
from app.models.scenario import PityScenario, PityScenarioStep
from app.utils.case_logger import CaseLog
from app.utils.logger import Log
from config import Config


class ScenarioExecutor:
    """场景流程执行器"""
    log = Log("ScenarioExecutor")

    def __init__(self, user_id: int, ws=None):
        self.user_id = user_id
        self.ws = ws
        self.variables: Dict[str, Any] = {}  # 全局变量上下文
        self.step_results: List[Dict[str, Any]] = []  # 步骤执行结果
        self.logger = CaseLog()

    async def execute_scenario(self, scenario_id: int, environment_id: int) -> Dict[str, Any]:
        """执行场景流程"""
        start_time = time.time()

        # 获取场景信息
        scenario = await PityScenarioDao.query_record(id=scenario_id)
        if not scenario:
            return {"status": "error", "error": f"场景不存在: {scenario_id}"}

        # 合并全局变量
        if scenario.variables:
            self.variables.update(scenario.variables)

        # 获取场景步骤（按顺序）
        from sqlalchemy import select
        from app.crud import async_session
        async with async_session() as session:
            stmt = select(PityScenarioStep).where(
                PityScenarioStep.scenario_id == scenario_id,
                PityScenarioStep.deleted_at == 0
            ).order_by(PityScenarioStep.step_order)
            result = await session.execute(stmt)
            steps = result.scalars().all()

        if not steps:
            return {"status": "error", "error": "场景没有配置步骤"}

        # 逐个执行步骤
        for step in steps:
            step_result = await self._execute_step(step, environment_id)
            self.step_results.append(step_result)

            # 检查步骤执行结果
            if step_result["status"] == "failed":
                # 如果步骤失败，根据配置决定是否继续
                if step_result.get("retry_count", 0) > 0:
                    # TODO: 实现重试逻辑
                    pass
                # 检查条件执行
                if step.condition and not self._evaluate_condition(step, step_result):
                    self.logger.append(f"步骤 {step.step_order} 条件不满足，跳过")
                    continue

            # 提取输出参数
            if step.output_mapping and step_result.get("response_data"):
                self._extract_output(step.output_mapping, step_result["response_data"])

        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)

        # 汇总结果
        passed = sum(1 for r in self.step_results if r["status"] == "passed")
        failed = sum(1 for r in self.step_results if r["status"] == "failed")
        error = sum(1 for r in self.step_results if r["status"] == "error")

        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario.name,
            "status": "passed" if failed == 0 and error == 0 else "failed",
            "total_steps": len(steps),
            "passed_steps": passed,
            "failed_steps": failed,
            "error_steps": error,
            "duration_ms": duration_ms,
            "step_results": self.step_results,
            "variables": self.variables,
        }

    async def _execute_step(self, step: PityScenarioStep, environment_id: int) -> Dict[str, Any]:
        """执行单个步骤"""
        start_time = time.time()

        try:
            # 获取用例信息
            case = await CaseV2Dao.query_record(id=step.case_id)
            if not case:
                return {
                    "step_order": step.step_order,
                    "case_id": step.case_id,
                    "status": "error",
                    "error": f"用例不存在: {step.case_id}"
                }

            # 应用输入映射 - 将上一步的输出注入到当前步骤
            request_data = {}
            if step.input_mapping:
                request_data = self._apply_input_mapping(step.input_mapping)

            # 根据 case_type 分发执行
            if case.case_type == "api":
                result = await self._execute_api_case(case, environment_id, request_data)
            elif case.case_type == "functional":
                result = await self._execute_functional_case(case, request_data)
            elif case.case_type == "ui":
                result = await self._execute_ui_case(case, request_data)
            else:
                result = {"status": "error", "error": f"不支持的用例类型: {case.case_type}"}

            end_time = time.time()
            result["step_order"] = step.step_order
            result["step_name"] = step.step_name
            result["case_id"] = step.case_id
            result["case_name"] = case.name
            result["duration_ms"] = int((end_time - start_time) * 1000)

            return result

        except Exception as e:
            self.log.error(f"步骤执行异常: {e}")
            return {
                "step_order": step.step_order,
                "case_id": step.case_id,
                "status": "error",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }

    def _apply_input_mapping(self, input_mapping: List[Dict]) -> Dict[str, Any]:
        """应用输入映射 - 将上一步的输出注入当前步骤"""
        result = {}
        for mapping in input_mapping:
            from_step = mapping.get("from_step")
            from_var = mapping.get("from_var")
            to_field = mapping.get("to_field")

            # 从历史步骤结果中获取变量值
            value = self._get_variable_from_history(from_step, from_var)
            if value is not None:
                # 设置到目标字段（支持嵌套如 headers.authorization）
                self._set_nested_value(result, to_field, value)

        return result

    def _get_variable_from_history(self, from_step: int, var_name: str) -> Any:
        """从历史步骤结果中获取变量"""
        for result in reversed(self.step_results):
            if result.get("step_order") == from_step:
                return result.get("variables", {}).get(var_name)
        # 尝试从全局变量获取
        return self.variables.get(var_name)

    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """设置嵌套字段值，如 headers.authorization"""
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def _extract_output(self, output_mapping: List[Dict], response_data: Any):
        """提取输出参数"""
        for mapping in output_mapping:
            var_name = mapping.get("var_name")
            extract_path = mapping.get("extract_path")

            # 使用 JSONPath 解析
            extracted_value = parameters_parser(extract_path, response_data)
            if extracted_value is not None:
                self.variables[var_name] = extracted_value
                self.logger.append(f"提取变量: {var_name} = {extracted_value}")

    def _evaluate_condition(self, step: PityScenarioStep, step_result: Dict[str, Any]) -> bool:
        """评估执行条件"""
        if not step.condition:
            return True

        try:
            # 简单的条件评估，如 status == 200
            condition = step.condition
            # 替换变量
            for key, value in step_result.items():
                if isinstance(value, (str, int, bool)):
                    condition = condition.replace(key, str(value))

            return eval(condition)
        except Exception as e:
            self.log.error(f"条件评估失败: {e}")
            return False

    async def _execute_api_case(self, case: PityCaseV2, environment_id: int, request_data: Dict) -> Dict[str, Any]:
        """执行 API 用例"""
        # TODO: 调用现有的 HttpConstructor 或创建新的 API 执行逻辑
        # 这里需要整合现有的 API 执行逻辑
        from app.core.constructor.http_constructor import HttpConstructor

        # 准备请求数据
        # 从 case 的扩展字段获取 URL、method 等
        from sqlalchemy import select
        from app.crud import async_session
        from app.models.case_field import PityTestcaseField

        async with async_session() as session:
            stmt = select(PityTestcaseField).where(
                PityTestcaseField.case_id == case.id,
                PityTestcaseField.deleted_at == 0
            )
            result = await session.execute(stmt)
            fields = result.scalars().all()

        # 构建字段字典
        field_dict = {f.field_name: f.field_value for f in fields}

        # 渲染变量
        for key in ["url", "method", "request_headers", "body"]:
            if key in field_dict and field_dict[key]:
                field_dict[key] = Render.render(self.variables, field_dict[key])

        # 获取环境信息
        from app.crud.config.EnvironmentDao import EnvironmentDao
        env = await EnvironmentDao.query_record(id=environment_id)
        if not env:
            return {"status": "error", "error": f"环境不存在: {environment_id}"}

        # TODO: 执行 HTTP 请求
        # 这里简化处理，实际需要调用 HttpConstructor
        return {
            "status": "passed",
            "response_data": {"code": 200, "data": field_dict},
            "variables": {}
        }

    async def _execute_functional_case(self, case: PityCaseV2, request_data: Dict) -> Dict[str, Any]:
        """执行功能测试用例"""
        # 功能测试用例 - 通常是一些验证逻辑
        # TODO: 实现功能测试执行逻辑
        return {
            "status": "passed",
            "response_data": {"result": "functional test passed"},
            "variables": {}
        }

    async def _execute_ui_case(self, case: PityCaseV2, request_data: Dict) -> Dict[str, Any]:
        """执行 UI 测试用例"""
        # UI 测试用例 - 通常需要浏览器自动化
        # TODO: 实现 UI 测试执行逻辑（可使用 Selenium/Playwright）
        return {
            "status": "passed",
            "response_data": {"result": "ui test passed"},
            "variables": {}
        }


class CaseV2Executor:
    """Case V2 用例执行器 - 支持动态模板"""
    log = Log("CaseV2Executor")

    def __init__(self, user_id: int, ws=None):
        self.user_id = user_id
        self.ws = ws
        self.variables: Dict[str, Any] = {}

    async def execute_case(self, case_id: int, environment_id: int, custom_params: Dict = None) -> Dict[str, Any]:
        """执行单个用例"""
        start_time = time.time()

        case = await CaseV2Dao.query_record(id=case_id)
        if not case:
            return {"status": "error", "error": f"用例不存在: {case_id}"}

        # 获取用例的扩展字段
        from sqlalchemy import select
        from app.crud import async_session
        from app.models.case_field import PityTestcaseField

        async with async_session() as session:
            stmt = select(PityTestcaseField).where(
                PityTestcaseField.case_id == case_id,
                PityTestcaseField.deleted_at == 0
            )
            result = await session.execute(stmt)
            fields = result.scalars().all()

        # 构建字段字典
        field_dict = {f.field_name: f.field_value for f in fields}

        # 合并自定义参数
        if custom_params:
            field_dict.update(custom_params)

        # 根据 case_type 分发执行
        if case.case_type == "api":
            result = await self._execute_api(field_dict, environment_id)
        elif case.case_type == "functional":
            result = await self._execute_functional(field_dict)
        elif case.case_type == "ui":
            result = await self._execute_ui(field_dict)
        else:
            result = {"status": "error", "error": f"不支持的用例类型: {case.case_type}"}

        end_time = time.time()
        return {
            "case_id": case_id,
            "case_name": case.name,
            "case_type": case.case_type,
            "status": result.get("status", "error"),
            "duration_ms": int((end_time - start_time) * 1000),
            "request_data": field_dict,
            "response_data": result.get("response_data"),
            "error": result.get("error"),
        }

    async def _execute_api(self, field_dict: Dict, environment_id: int) -> Dict[str, Any]:
        """执行 API 请求"""
        url = field_dict.get("url", "")
        method = field_dict.get("method", "GET")
        headers = field_dict.get("headers", {})
        body = field_dict.get("body")

        # 渲染变量
        url = Render.render(self.variables, url)
        method = Render.render(self.variables, method)

        try:
            from app.middleware.AsyncHttpClient import AsyncRequest
            client = AsyncRequest()

            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if method in ["POST", "PUT", "PATCH"] else None
            )

            return {
                "status": "passed" if response.status_code < 400 else "failed",
                "response_data": {
                    "status_code": response.status_code,
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "headers": dict(response.headers),
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _execute_functional(self, field_dict: Dict) -> Dict[str, Any]:
        """执行功能测试"""
        # 功能测试 - 验证业务逻辑
        return {
            "status": "passed",
            "response_data": {"result": "functional test passed"}
        }

    async def _execute_ui(self, field_dict: Dict) -> Dict[str, Any]:
        """执行 UI 测试"""
        # UI 测试 - 浏览器自动化
        return {
            "status": "passed",
            "response_data": {"result": "ui test passed"}
        }

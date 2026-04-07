"""
AI 异步任务

使用 Celery 处理耗时的 AI 任务
"""
import asyncio
import json
from typing import Any, Dict, List

from celery import Task
from celery_app import celery_app
from loguru import logger


class AICallbackTask(Task):
    """带回调的 AI 任务基类"""

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        logger.bind(name="celery").info(f"AI Task {task_id} succeeded: {retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.bind(name="celery").error(f"AI Task {task_id} failed: {exc}")


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


async def _save_case_sync(case_config: dict, project_id: int, user_id: int, priority: str, status: int):
    """同步保存生成的用例到数据库"""
    import json
    from app.models import async_session
    from app.crud.test_case.TestCaseDao import TestCaseDao
    from app.schema.testcase_schema import TestCaseForm, TestCaseInfo, TestCaseAssertsForm

    body_data = case_config.get("body")
    headers_data = case_config.get("request_headers")

    case_form = TestCaseForm(
        name=case_config.get("name", "AI 生成用例"),
        url=case_config.get("url", "/"),
        project_id=project_id,
        priority=priority,
        status=status,
        request_type=1,
        request_method=case_config.get("request_method", "POST"),
        body_type=case_config.get("body_type", 0),
        body=json.dumps(body_data, ensure_ascii=False) if body_data else "{}",
        request_headers=json.dumps(headers_data, ensure_ascii=False) if headers_data else "{}",
    )

    asserts = []
    for idx, a in enumerate(case_config.get("asserts", [])):
        assert_type = a.get("assert_type", "equal")
        expected = str(a.get("expected", ""))
        actually = str(a.get("actually", ""))

        if not actually:
            if assert_type == "status_code":
                actually = "$.status_code"
            elif assert_type == "equal":
                actually = "$.code"
            else:
                actually = "$.data"

        if not expected:
            continue

        asserts.append(TestCaseAssertsForm(
            name=f"断言_{idx + 1}",
            assert_type=assert_type,
            expected=expected,
            actually=actually,
        ))

    case_info = TestCaseInfo(
        case=case_form,
        asserts=asserts if asserts else [],
    )

    async with async_session() as session:
        async with session.begin():
            case = await TestCaseDao.insert_test_case(session, case_info, user_id)
            return case.id


@celery_app.task(
    base=AICallbackTask,
    bind=True,
    name='ai.generate_testcase'
)
def generate_testcase(self, content: str, input_type: str, model: str = None, **kwargs) -> Dict[str, Any]:
    """
    异步生成测试用例

    Args:
        content: 输入内容（API描述/cURL/OpenAPI）
        input_type: 输入类型 text/curl/openapi
        model: AI 模型名称
        directory_id: 用例目录 ID（用于保存）
        user_id: 用户 ID
        priority: 用例优先级
        status: 用例状态

    Returns:
        生成的用例配置
    """
    from app.core.ai.factory import get_ai_service
    from config import Config

    project_id = kwargs.get("project_id")
    user_id = kwargs.get("user_id")
    priority = kwargs.get("priority", "P3")
    status = kwargs.get("status", 3)

    model = model or None
    ai_service = run_async(get_ai_service(model_name=model))

    try:
        if input_type == "text":
            result = run_async(ai_service.generate_testcase(content))
        elif input_type == "curl":
            result = run_async(ai_service.parse_curl(content))
        elif input_type == "openapi":
            result = run_async(ai_service.batch_generate_from_openapi(content))
        else:
            return {"status": "error", "error": f"不支持的输入类型: {input_type}"}

        # 保存到数据库
        if project_id and user_id:
            case_id = run_async(_save_case_sync(result, project_id, user_id, priority, status))
            result["case_id"] = case_id
            logger.bind(name="celery").info(f"用例已保存到数据库，case_id={case_id}")

        return {
            "status": "success",
            "result": result,
            "model": model,
        }
    except Exception as e:
        logger.bind(name="celery").error(f"生成用例失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "model": model,
        }


async def _save_asserts_sync(case_id: int, asserts: list, user_id: int) -> list:
    """同步保存断言到数据库"""
    from app.models import async_session
    from app.crud.test_case.TestCaseAssertsDao import TestCaseAssertsDao
    from app.schema.testcase_schema import TestCaseAssertsForm

    saved = []
    for idx, a in enumerate(asserts):
        assert_type = a.get("assert_type", "equal")
        expected = str(a.get("expected", ""))
        actually = str(a.get("actually", ""))

        if not actually:
            if assert_type == "status_code":
                actually = "$.status_code"
            elif assert_type == "equal":
                actually = "$.code"
            else:
                actually = "$.data"

        if not expected:
            continue

        try:
            assert_form = TestCaseAssertsForm(
                name=f"AI断言_{idx + 1}",
                case_id=case_id,
                assert_type=assert_type,
                expected=expected,
                actually=actually,
            )
            async with async_session() as session:
                async with session.begin():
                    record = await TestCaseAssertsDao.insert_test_case_asserts(session, assert_form, user_id)
                    saved.append({
                        "id": record.id,
                        "assert_type": assert_type,
                        "expected": expected,
                        "actually": actually,
                    })
        except Exception:
            continue
    return saved


@celery_app.task(
    base=AICallbackTask,
    bind=True,
    name='ai.enhance_asserts'
)
def enhance_asserts(self, case_id: int, case_info: Dict, response_sample: str, model: str = None, **kwargs) -> Dict[str, Any]:
    """
    异步增强用例断言

    Args:
        case_id: 用例 ID
        case_info: 用例信息
        response_sample: 响应示例
        model: AI 模型名称
        user_id: 用户 ID

    Returns:
        生成的断言列表
    """
    from app.core.ai.factory import get_ai_service
    from config import Config

    user_id = kwargs.get("user_id")

    model = model or None
    ai_service = run_async(get_ai_service(model_name=model))

    try:
        result = run_async(ai_service.enhance_asserts(case_info, response_sample))

        # 保存断言到数据库
        saved_asserts = []
        if user_id:
            saved_asserts = run_async(_save_asserts_sync(case_id, result, user_id))
            logger.bind(name="celery").info(f"断言已保存，case_id={case_id}, count={len(saved_asserts)}")

        return {
            "status": "success",
            "case_id": case_id,
            "asserts": result,
            "saved_count": len(saved_asserts),
            "model": model,
        }
    except Exception as e:
        logger.bind(name="celery").error(f"增强断言失败: {e}")
        return {
            "status": "error",
            "case_id": case_id,
            "error": str(e),
            "model": model,
        }


@celery_app.task(
    base=AICallbackTask,
    bind=True,
    name='ai.batch_generate'
)
def batch_generate(self, openapi_spec: str, max_cases: int = 20, model: str = None, **kwargs) -> Dict[str, Any]:
    """
    异步批量生成测试用例

    Args:
        openapi_spec: OpenAPI 规范
        max_cases: 最大用例数量
        model: AI 模型名称
        directory_id: 用例目录 ID
        user_id: 用户 ID
        priority: 用例优先级
        status: 用例状态

    Returns:
        生成的用例列表
    """
    from app.core.ai.factory import get_ai_service
    from config import Config

    project_id = kwargs.get("project_id")
    user_id = kwargs.get("user_id")
    priority = kwargs.get("priority", "P3")
    status = kwargs.get("status", 3)

    model = model or None
    ai_service = run_async(get_ai_service(model_name=model))

    try:
        cases_config = run_async(ai_service.batch_generate_from_openapi(openapi_spec, max_cases=max_cases))

        # 保存到数据库
        saved_cases = []
        if project_id and user_id:
            for case_config in cases_config:
                try:
                    case_id = run_async(_save_case_sync(case_config, project_id, user_id, priority, status))
                    saved_cases.append({"case_id": case_id, "name": case_config.get("name", "")})
                    logger.bind(name="celery").info(f"批量生成用例已保存，case_id={case_id}")
                except Exception as e:
                    logger.bind(name="celery").warning(f"保存用例失败: {e}")
                    continue

        return {
            "status": "success",
            "cases": cases_config,
            "saved": saved_cases,
            "count": len(cases_config) if isinstance(cases_config, list) else 0,
            "saved_count": len(saved_cases),
            "model": model,
        }
    except Exception as e:
        logger.bind(name="celery").error(f"批量生成用例失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "model": model,
        }

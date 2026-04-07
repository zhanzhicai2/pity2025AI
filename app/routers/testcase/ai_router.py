from typing import List

from fastapi import APIRouter, Depends
from loguru import logger

from app.core.ai.factory import get_ai_service
from app.handler.fatcory import PityResponse
from app.routers import Permission
from app.services.rag_service import VectorStoreService
from app.schema.ai_schema import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIEnhanceRequest,
    BatchGenerateRequest,
    BatchGenerateResponse,
    CURLParseRequest,
    GeneratedCaseResponse,
    AIModelsResponse,
    AIModelInfo,
)
from config import Config

router = APIRouter(prefix="/testcase/ai", tags=["AI 测试用例生成"])


# ==================== 异步任务端点 ====================

@router.post("/generate/async", response_model=dict)
async def generate_testcase_async(
    form: AIGenerateRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 异步生成测试用例（Celery 后台执行）

    返回任务 ID，前端通过 /task/{task_id} 查询状态
    """
    from app.tasks.ai_tasks import generate_testcase
    from config import Config

    model = form.model or None
    user_id = user_info.get("id")

    # 触发 Celery 异步任务
    task = generate_testcase.delay(
        content=form.content,
        input_type=form.input_type,
        model=model,
        project_id=form.project_id,
        user_id=user_id,
        priority=form.priority,
        status=form.status,
    )

    return PityResponse.success({
        "task_id": task.id,
        "status": task.state,
        "message": "任务已提交，请在 /task/{task_id} 查询进度",
    })


@router.post("/enhance/async", response_model=dict)
async def enhance_case_asserts_async(
    form: AIEnhanceRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 异步增强用例断言（Celery 后台执行）

    返回任务 ID，前端通过 /task/{task_id} 查询状态
    """
    import json
    from app.tasks.ai_tasks import enhance_asserts
    from app.crud.test_case.TestCaseDao import TestCaseDao
    from config import Config

    user_id = user_info.get("id")
    model = form.model or None

    # 获取用例信息
    case = await TestCaseDao.async_query_test_case(form.case_id)
    if case is None:
        return PityResponse.failed(msg="用例不存在")

    case_info = {
        "name": case.name,
        "url": case.url,
        "request_method": case.request_method,
        "body": json.loads(case.body) if case.body else {},
    }

    # 触发 Celery 异步任务
    task = enhance_asserts.delay(
        case_id=form.case_id,
        case_info=case_info,
        response_sample=form.response_sample,
        model=model,
        user_id=user_id,
    )

    return PityResponse.success({
        "task_id": task.id,
        "status": task.state,
        "message": "任务已提交，请在 /task/{task_id} 查询进度",
    })


@router.post("/batch-generate/async", response_model=dict)
async def batch_generate_testcases_async(
    form: BatchGenerateRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 异步批量生成测试用例（Celery 后台执行）

    返回任务 ID，前端通过 /task/{task_id} 查询状态
    """
    from app.tasks.ai_tasks import batch_generate
    from config import Config

    model = form.model or None
    user_id = user_info.get("id")

    # 触发 Celery 异步任务
    task = batch_generate.delay(
        openapi_spec=form.openapi_spec,
        max_cases=form.max_cases,
        model=model,
        project_id=form.project_id,
        user_id=user_id,
        priority=form.priority,
        status=form.status,
    )

    return PityResponse.success({
        "task_id": task.id,
        "status": task.state,
        "message": "任务已提交，请在 /task/{task_id} 查询进度",
    })


# ==================== 同步任务端点（保留原有逻辑）====================

@router.post("/generate", response_model=dict)
async def generate_testcase(
    form: AIGenerateRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 生成测试用例

    根据自然语言描述、OpenAPI Schema、cURL 等输入生成测试用例
    """
    model = form.model or None

    ai_service = await get_ai_service(model_name=model)

    # 根据输入类型调用不同的生成方法
    user_id = user_info.get("id")
    if form.input_type == "text":
        rag_docs = ""
        if form.use_rag:
            try:
                vs = VectorStoreService.get_instance()
                rag_results = vs.similarity_search_with_rerank(form.content, top_k=5, initial_k=20)
                if rag_results.get("results"):
                    docs_text = "\n\n".join([
                        f"【文档 {i+1}】{r['content']}"
                        for i, r in enumerate(rag_results["results"])
                    ])
                    rag_docs = docs_text
                    logger.bind(name=Config.PITY_INFO).info(f"RAG 检索到 {len(rag_results['results'])} 条相关文档")
            except Exception as e:
                logger.bind(name=Config.PITY_ERROR).warning(f"RAG 检索失败: {e}")

        result = await ai_service.generate_testcase(form.content, rag_docs=rag_docs)
        # 保存到数据库
        case = await _save_generated_case(form, result, user_id)
        return PityResponse.success({
            "case_id": case.id,
            "name": result.get("name", "AI 生成用例"),
            "url": result.get("url", "/"),
            "request_method": result.get("request_method", "POST"),
            "body_type": result.get("body_type", 0),
            "body": result.get("body"),
            "request_headers": result.get("request_headers"),
            "asserts": result.get("asserts", []),
            "model": model,
        })
    elif form.input_type == "curl":
        result = await ai_service.parse_curl(form.content)
        # 保存到数据库
        case = await _save_generated_case(form, result, user_id)
        return PityResponse.success({
            "case_id": case.id,
            "name": result.get("name", "AI 生成用例"),
            "url": result.get("url", "/"),
            "request_method": result.get("request_method", "POST"),
            "body_type": result.get("body_type", 0),
            "body": result.get("body"),
            "request_headers": result.get("request_headers"),
            "asserts": result.get("asserts", []),
            "model": model,
        })
    elif form.input_type == "openapi":
        result = await ai_service.batch_generate_from_openapi(form.content)
        return PityResponse.success({
            "cases": result,
            "model": model,
        })
    else:
        return PityResponse.failed(msg=f"不支持的输入类型: {form.input_type}")


@router.post("/enhance", response_model=dict)
async def enhance_case_asserts(
    form: AIEnhanceRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 增强用例断言

    根据已有用例和响应示例生成智能断言，并保存到数据库
    """
    import json
    from app.crud.test_case.TestCaseDao import TestCaseDao
    from app.crud.test_case.TestCaseAssertsDao import TestCaseAssertsDao
    from app.schema.testcase_schema import TestCaseAssertsForm

    user_id = user_info.get("id")

    # 获取用例信息
    case = await TestCaseDao.async_query_test_case(form.case_id)
    if case is None:
        return PityResponse.failed(msg="用例不存在")

    # 调用 AI 生成断言
    ai_service = await get_ai_service(model_name=model)
    case_info = {
        "name": case.name,
        "url": case.url,
        "request_method": case.request_method,
        "body": json.loads(case.body) if case.body else {},
    }
    ai_asserts = await ai_service.enhance_asserts(case_info, form.response_sample)

    # 保存断言到数据库
    saved_asserts = []
    for idx, a in enumerate(ai_asserts):
        assert_type = a.get("assert_type", "equal")
        expected = str(a.get("expected", ""))
        actually = str(a.get("actually", ""))

        # 设置默认值
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
                case_id=form.case_id,
                assert_type=assert_type,
                expected=expected,
                actually=actually,
            )
            saved = await TestCaseAssertsDao.insert_test_case_asserts(assert_form, user_id)
            saved_asserts.append({
                "id": saved.id,
                "assert_type": assert_type,
                "expected": expected,
                "actually": actually,
            })
        except Exception as e:
            # 断言已存在则跳过
            continue

    return PityResponse.success({
        "case_id": form.case_id,
        "asserts": saved_asserts,
        "total": len(saved_asserts),
        "model": form.model or None,
    })


@router.post("/batch-generate", response_model=dict)
async def batch_generate_testcases(
    form: BatchGenerateRequest,
    user_info: dict = Depends(Permission()),
):
    """
    批量生成测试用例

    从 OpenAPI 规范批量生成测试用例
    """
    from app.crud.test_case.TestCaseDao import TestCaseDao

    user_id = user_info.get("id")
    model = form.model or None

    ai_service = await get_ai_service(model_name=model)
    cases_config = await ai_service.batch_generate_from_openapi(
        form.openapi_spec,
        max_cases=form.max_cases
    )

    saved_cases = []
    failed_count = 0

    for case_config in cases_config:
        try:
            # 构建保存请求
            request = AIGenerateRequest(
                project_id=form.project_id,
                input_type="openapi",
                content=str(case_config),
                model=model,
                priority=form.priority,
                status=form.status,
            )
            case = await _save_generated_case(request, case_config, user_id)
            saved_cases.append(case)
        except Exception as e:
            failed_count += 1

    return PityResponse.success({
        "total": len(cases_config),
        "cases": [
            {
                "case_id": c.id,
                "name": c.name,
                "url": c.url,
                "request_method": c.request_method,
            }
            for c in saved_cases
        ],
        "model": model,
        "failed_count": failed_count,
    })


@router.post("/parse-curl", response_model=dict)
async def parse_curl(
    form: CURLParseRequest,
    user_info: dict = Depends(Permission()),
):
    """
    解析 cURL 命令生成用例
    """
    user_id = user_info.get("id")
    model = form.model or None

    ai_service = await get_ai_service(model_name=model)
    result = await ai_service.parse_curl(form.curl_command)

    # 保存用例
    request = AIGenerateRequest(
        project_id=form.project_id,
        input_type="curl",
        content=form.curl_command,
        model=model,
        priority=form.priority,
        status=form.status,
    )
    case = await _save_generated_case(request, result, user_id)

    return PityResponse.success({
        "case_id": case.id,
        "name": case.name,
        "url": case.url,
        "request_method": case.request_method,
        "body_type": case.body_type,
        "body": case.body,
        "request_headers": case.request_headers,
        "asserts": result.get("asserts", []),
        "model": model,
    })


@router.get("/models", response_model=dict)
async def list_models():
    """
    获取可用 AI 模型列表（从数据库读取）
    """
    from app.crud.llm_config import LLMConfigDao

    configs = await LLMConfigDao.list_configs(is_active=True)
    default_config = await LLMConfigDao.get_default()

    default_model_name = default_config.name if default_config else None

    models = [
        AIModelInfo(
            name=c.name,
            display_name=f"{c.name} ({c.provider})",
            description=f"{c.config_name} - {c.provider}",
            is_default=(default_config and c.id == default_config.id),
        )
        for c in configs
    ]

    return PityResponse.success({
        "models": [m.model_dump() for m in models],
        "default_model": default_model_name,
    })


@router.post("/generate/graph", response_model=dict)
async def generate_testcase_with_graph(
    form: AIGenerateRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 生成测试用例（LangGraph 工作流）

    支持 RAG 检索 -> AI 生成 -> 自我审查 的完整流程
    """
    from app.core.ai.graph.builder import build_case_generation_graph

    user_id = user_info.get("id")

    # 构建并执行 Graph
    graph = build_case_generation_graph()
    initial_state = {
        "api_description": form.content,
        "user_id": user_id,
        "use_rag": form.use_rag,
        "rag_docs": [],
        "generated_case": None,
        "review_result": None,
        "error": None,
        "final_case": None,
        "success": False,
    }

    result = await graph.ainvoke(initial_state)

    if not result.get("success"):
        return PityResponse.failed(msg=result.get("error", "生成失败"))

    generated_case = result.get("generated_case", {})
    if not generated_case:
        return PityResponse.failed(msg="未生成有效用例")

    # 保存到数据库
    case = await _save_generated_case(form, generated_case, user_id)

    return PityResponse.success({
        "case_id": case.id,
        "name": generated_case.get("name", "AI 生成用例"),
        "url": generated_case.get("url", "/"),
        "request_method": generated_case.get("request_method", "POST"),
        "body_type": generated_case.get("body_type", 0),
        "body": generated_case.get("body"),
        "request_headers": generated_case.get("request_headers"),
        "asserts": generated_case.get("asserts", []),
        "review_result": result.get("review_result"),
        "use_rag": form.use_rag,
    })


# ==================== 内部方法 ====================

async def _save_generated_case(form: AIGenerateRequest, config: dict, user_id: int):
    """
    保存 AI 生成的用例
    """
    import json
    from app.crud.test_case.TestCaseDao import TestCaseDao
    from app.schema.testcase_schema import (
        TestCaseForm,
        TestCaseInfo,
        TestCaseAssertsForm,
    )

    # 构建用例表单
    body_data = config.get("body")
    headers_data = config.get("request_headers")

    case_form = TestCaseForm(
        name=config.get("name", "AI 生成用例"),
        url=config.get("url", "/"),
        project_id=form.project_id,
        priority=form.priority,
        status=form.status,
        request_type=1,  # HTTP
        request_method=config.get("request_method", "POST"),
        body_type=config.get("body_type", 0),
        body=json.dumps(body_data, ensure_ascii=False) if body_data else "{}",
        request_headers=json.dumps(headers_data, ensure_ascii=False) if headers_data else "{}",
    )

    # 构建断言
    asserts = []
    for idx, a in enumerate(config.get("asserts", [])):
        assert_type = a.get("assert_type", "equal")
        expected = str(a.get("expected", ""))
        actually = str(a.get("actually", ""))

        # 如果 actually 为空，根据 assert_type 设置默认值
        if not actually:
            if assert_type == "status_code":
                actually = "$.status_code"
            elif assert_type == "equal":
                actually = "$.code"
            else:
                actually = "$.data"

        # 跳过空的断言
        if not expected:
            continue

        asserts.append(TestCaseAssertsForm(
            name=f"断言_{idx + 1}",
            assert_type=assert_type,
            expected=expected,
            actually=actually,
        ))

    # 构建完整用例信息
    case_info = TestCaseInfo(
        case=case_form,
        asserts=asserts if asserts else [],
    )

    # 保存
    from app.models import async_session
    async with async_session() as session:
        async with session.begin():
            case = await TestCaseDao.insert_test_case(session, case_info, user_id)
            return case

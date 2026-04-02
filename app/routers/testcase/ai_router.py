from typing import List

from fastapi import APIRouter, Depends

from app.core.ai import OpenAIService
from app.handler.fatcory import PityResponse
from app.routers import Permission
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


@router.post("/generate", response_model=dict)
async def generate_testcase(
    form: AIGenerateRequest,
    user_info: dict = Depends(Permission()),
):
    """
    AI 生成测试用例

    根据自然语言描述、OpenAPI Schema、cURL 等输入生成测试用例
    """
    model = form.model or Config.AI_MODEL

    ai_service = OpenAIService()

    # 根据输入类型调用不同的生成方法
    user_id = user_info.get("id")
    if form.input_type == "text":
        result = await ai_service.generate_testcase(form.content)
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
    ai_service = OpenAIService()
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
        "model": form.model or Config.AI_MODEL,
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
    model = form.model or Config.AI_MODEL

    ai_service = OpenAIService()
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
                directory_id=form.directory_id,
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
    model = form.model or Config.AI_MODEL

    ai_service = OpenAIService()
    result = await ai_service.parse_curl(form.curl_command)

    # 保存用例
    request = AIGenerateRequest(
        directory_id=form.directory_id,
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
    获取可用 AI 模型列表
    """
    default_model = Config.AI_MODEL
    models = [
        AIModelInfo(
            name="MiniMax-M2.7",
            display_name="MiniMax M2.7",
            description="MiniMax 最新模型，适合中文场景",
            is_default=(default_model == "MiniMax-M2.7"),
        ),
        AIModelInfo(
            name="gpt-4o",
            display_name="GPT-4o",
            description="OpenAI 最新模型，能力最强",
            is_default=(default_model == "gpt-4o"),
        ),
        AIModelInfo(
            name="gpt-4o-mini",
            display_name="GPT-4o Mini",
            description="OpenAI 轻量模型，性价比高",
            is_default=(default_model == "gpt-4o-mini"),
        ),
        AIModelInfo(
            name="claude-3-5-sonnet",
            display_name="Claude 3.5 Sonnet",
            description="Anthropic 中等能力模型",
            is_default=(default_model == "claude-3-5-sonnet"),
        ),
    ]

    return PityResponse.success({
        "models": [m.model_dump() for m in models],
        "default_model": default_model,
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
        directory_id=form.directory_id,
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

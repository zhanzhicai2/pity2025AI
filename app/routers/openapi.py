"""
OpenAPI 导入 API 路由
"""
from fastapi import APIRouter, Depends

from app.core.openapi_parser import openapi_parser
from app.routers import Permission
from app.schema.openapi import OpenAPIParseForm, OpenAPIGenerateForm
from app.utils.logger import Log

logger = Log("openapi_router")
router = APIRouter(prefix="/import/openapi", tags=["OpenAPI导入"])


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


@router.post("/parse", summary="解析 OpenAPI 文档")
async def parse_openapi(
    form: OpenAPIParseForm,
    user_info: dict = Depends(get_current_user)
):
    """解析 OpenAPI JSON/YAML 文档，返回 API 列表"""
    try:
        if form.url:
            result = await openapi_parser.parse_url(form.url)
        elif form.content:
            result = openapi_parser.parse_content(form.content)
        else:
            return {"code": 110, "data": None, "msg": "请提供 URL 或 content"}

        return {"code": 0, "data": result, "msg": "解析成功"}
    except Exception as e:
        logger.error(f"解析 OpenAPI 文档失败: {e}")
        return {"code": 110, "data": None, "msg": f"解析失败: {str(e)}"}


@router.post("/generate", summary="生成测试用例")
async def generate_testcases(
    form: OpenAPIGenerateForm,
    user_info: dict = Depends(get_current_user)
):
    """根据解析的 API 生成测试用例"""
    try:
        # TODO: 调用测试用例创建服务生成用例
        # 这里先返回模拟数据
        result = {
            "generated": len(form.apis),
            "apis": form.apis,
            "message": "用例生成功能开发中"
        }
        return {"code": 0, "data": result, "msg": "生成成功"}
    except Exception as e:
        logger.error(f"生成测试用例失败: {e}")
        return {"code": 110, "data": None, "msg": f"生成失败: {str(e)}"}

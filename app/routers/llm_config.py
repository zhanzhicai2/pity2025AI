"""
LLM 配置路由
"""
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query

from app.crud.llm_config import LLMConfigDao
from app.exception.error import ParamsError
from app.handler.fatcory import PityResponse
from app.models.llm_config import LLMConfig
from app.routers import Permission
from app.schema.llm_config import (
    LLMConfigCreateSchema,
    LLMConfigUpdateSchema,
    LLMConfigTestSchema,
    LLMConfigTestResponseSchema,
)
from app.utils.logger import Log

router = APIRouter(prefix="/llm/config", tags=["LLM 配置"])
logger = Log("llm_config_router")


def get_current_user(user_info=Depends(Permission())):
    """获取当前用户"""
    return user_info


@router.get("")
async def list_configs(
    provider: Optional[str] = Query(None, description="提供商筛选"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选"),
    user_info: dict = Depends(get_current_user),
):
    """获取 LLM 配置列表"""
    configs = await LLMConfigDao.list_configs(provider=provider, is_active=is_active)
    return PityResponse.success_with_size(configs)


@router.get("/default")
async def get_default_config(
    user_info: dict = Depends(get_current_user),
):
    """获取默认配置"""
    config = await LLMConfigDao.get_default()
    return PityResponse.success(config)


@router.get("/{config_id}")
async def get_config(
    config_id: int,
    user_info: dict = Depends(get_current_user),
):
    """获取配置详情"""
    config = await LLMConfigDao.get_by_id(config_id=config_id)
    if not config:
        raise ParamsError("配置不存在")
    return PityResponse.success(config)


@router.post("")
async def create_config(
    data: LLMConfigCreateSchema,
    user_info: dict = Depends(get_current_user),
):
    """创建 LLM 配置"""
    # 如果设置为默认配置，先取消其他默认配置
    if data.is_default:
        await LLMConfigDao.unset_all_defaults()

    config = LLMConfig(
        user=user_info['id'],
        config_name=data.config_name,
        name=data.name,
        provider=data.provider,
        model_name=data.model_name,
        api_key=data.api_key,
        base_url=data.base_url,
        system_prompt=data.system_prompt,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        supports_vision=data.supports_vision,
        context_limit=data.context_limit,
        is_default=data.is_default,
        is_active=data.is_active,
    )

    result = await LLMConfigDao.insert(model=config)
    return PityResponse.success(result)


@router.put("/{config_id}")
async def update_config(
    config_id: int,
    data: LLMConfigUpdateSchema,
    user_info: dict = Depends(get_current_user),
):
    """更新 LLM 配置"""
    config = await LLMConfigDao.get_by_id(config_id=config_id)
    if not config:
        raise ParamsError("配置不存在")

    # 如果设置为默认配置，先取消其他默认配置
    if data.is_default:
        await LLMConfigDao.unset_all_defaults()

    # 检查 API Key 是否是脱敏值，如果是则保留原值
    update_data = data.model_dump(exclude_unset=True)
    if update_data.get('api_key') and '****' in str(update_data.get('api_key')):
        logger.bind(name="llm_config").info("检测到脱敏的API Key，保留原值")
        del update_data['api_key']

    result = await LLMConfigDao.update_config(config_id, user_info['id'], **update_data)
    return PityResponse.success(result)


@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    user_info: dict = Depends(get_current_user),
):
    """删除 LLM 配置"""
    success = await LLMConfigDao.delete_config(config_id, user_info['id'])
    if not success:
        raise ParamsError("配置不存在")
    return {"code": 0, "msg": "删除成功"}


@router.post("/{config_id}/set-default")
async def set_default_config(
    config_id: int,
    user_info: dict = Depends(get_current_user),
):
    """设为默认配置"""
    config = await LLMConfigDao.set_default(config_id)
    if not config:
        raise ParamsError("配置不存在")
    return PityResponse.success(config)


@router.post("/test", response_model=LLMConfigTestResponseSchema)
async def test_config(
    data: LLMConfigTestSchema,
    user_info: dict = Depends(get_current_user),
):
    """测试 LLM 配置"""
    start_time = time.time()

    # 如果提供了 config_id，从数据库加载配置
    if data.config_id:
        config = await LLMConfigDao.get_by_id(config_id=data.config_id)
        if not config:
            return LLMConfigTestResponseSchema(
                success=False,
                message="配置不存在",
                error="配置ID无效"
            )
        provider = config.provider
        api_key = config.api_key
        base_url = config.base_url
        model_name = config.name
    else:
        # 使用提供的临时配置
        provider = data.provider
        api_key = data.api_key
        base_url = data.base_url
        model_name = data.name

    # 验证必要字段
    if not api_key or not base_url or not model_name:
        return LLMConfigTestResponseSchema(
            success=False,
            message="测试失败",
            error="API Key、Base URL 和模型名称不能为空"
        )

    # 测试连接
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": data.test_message}
            ],
            "max_tokens": 100
        }

        # 确定端点
        endpoint = f"{base_url.rstrip('/')}/chat/completions"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)

            latency = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return LLMConfigTestResponseSchema(
                    success=True,
                    message="测试成功",
                    response=content,
                    latency=round(latency, 2)
                )
            else:
                return LLMConfigTestResponseSchema(
                    success=False,
                    message="测试失败",
                    error=f"HTTP {response.status_code}: {response.text[:500]}",
                    latency=round(latency, 2)
                )

    except httpx.TimeoutException:
        return LLMConfigTestResponseSchema(
            success=False,
            message="测试失败",
            error="请求超时，请检查网络连接或增加超时时间"
        )
    except Exception as e:
        latency = time.time() - start_time
        logger.bind(name="llm_config").error(f"LLM 配置测试异常: {str(e)}")
        return LLMConfigTestResponseSchema(
            success=False,
            message="测试失败",
            error=str(e),
            latency=round(latency, 2)
        )

"""
AI 服务工厂
根据数据库中的 LLM 配置动态获取 AI 服务实例
所有 AI 功能统一使用默认配置的 LLM 大模型
"""
from typing import Optional

from app.crud.llm_config import LLMConfigDao
from app.core.ai.openai_service import OpenAIService


async def get_ai_service(config_id: Optional[int] = None, model_name: Optional[str] = None) -> OpenAIService:
    """
    获取 AI 服务实例

    优先级：
    1. config_id - 直接指定配置 ID
    2. model_name - 按模型名称查找对应配置
    3. 默认配置（is_default=True）
    4. 第一个可用配置
    5. 抛出异常提示用户配置

    Args:
        config_id: LLM 配置 ID，优先级最高
        model_name: 模型名称，优先级次之

    Returns:
        OpenAIService 实例

    Raises:
        Exception: 当没有可用配置时，提示用户去设置默认大模型
    """
    configs = await LLMConfigDao.list_configs(is_active=True)
    if not configs:
        raise Exception(
            "请先在 LLM 配置页面 (/ai/config) 添加并设置为默认的大模型配置"
        )

    config = None

    # 1. 指定配置 ID
    if config_id is not None:
        config = await LLMConfigDao.get_by_id(config_id)
        if config and config.is_active:
            return _create_service(config)

    # 2. 按模型名称查找
    if model_name is not None:
        config = next((c for c in configs if c.name == model_name), None)
        if config and config.is_active:
            return _create_service(config)

    # 3. 回退到默认配置
    config = await LLMConfigDao.get_default()
    if config and config.is_active:
        return _create_service(config)

    # 4. 回退到第一个可用配置
    if configs:
        return _create_service(configs[0])

    # 5. 没有可用配置
    raise Exception(
        "请先在 LLM 配置页面 (/ai/config) 添加并设置为默认的大模型配置"
    )


def _create_service(config) -> OpenAIService:
    """创建 AI 服务实例"""
    return OpenAIService(
        api_key=config.api_key or "",
        base_url=config.base_url or "",
        model_name=config.name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        provider=config.provider,
    )


async def get_default_ai_config():
    """获取默认 AI 配置"""
    return await LLMConfigDao.get_default()

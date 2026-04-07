"""
LLM 配置数据模型
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, INT

from app.models.basic import PityBase


class LLMConfig(PityBase):
    """LLM 配置模型"""
    __tablename__ = "sys_llm_config"
    __table_args__ = {'comment': 'LLM 配置表', 'mysql_charset': 'utf8mb4'}
    __fields__ = (id,)
    __tag__ = "LLM配置"
    __alias__ = dict(name="名称")

    def __init__(self, user, config_name=None, name=None, provider=None, model_name=None,
                 api_key=None, base_url=None, system_prompt=None, temperature=0.7,
                 max_tokens=2000, supports_vision=False, context_limit=128000,
                 is_default=False, is_active=True, id=None):
        super().__init__(user, id)
        self.config_name = config_name
        self.name = name
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.supports_vision = supports_vision
        self.context_limit = context_limit
        self.is_default = is_default
        self.is_active = is_active

    # 配置标识字段
    config_name = Column(
        String(255),
        nullable=False,
        comment="用户自定义的配置名称，如'生产环境OpenAI'"
    )

    # 模型信息
    name = Column(String(100), nullable=False, comment="模型名称，如 gpt-4, claude-3-sonnet")
    provider = Column(String(50), nullable=False, comment="LLM 提供商: openai/anthropic/ollama/custom")
    model_name = Column(String(100), nullable=False, comment="模型名称（兼容字段）")

    # API 配置
    api_key = Column(String(500), nullable=True, comment="API 密钥（本地模型如 Ollama 可为空）")
    base_url = Column(String(500), nullable=True, comment="API 基础URL")

    # 系统提示词
    system_prompt = Column(
        Text,
        nullable=True,
        comment="指导LLM行为的系统级提示词"
    )

    # 模型参数
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=2000, comment="最大令牌数")

    # 多模态支持
    supports_vision = Column(
        Boolean,
        default=False,
        comment="模型是否支持图片/多模态输入（如GPT-4V）"
    )

    # 上下文限制
    context_limit = Column(
        Integer,
        default=128000,
        comment="模型最大上下文Token数"
    )

    # 状态字段
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    is_active = Column(Boolean, default=True, comment="是否启用")

    def __repr__(self):
        return f'<LLMConfig {self.config_name} ({self.provider})>'

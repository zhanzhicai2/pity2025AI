from abc import ABC, abstractmethod
from typing import Optional


class AIService(ABC):
    """AI 服务基类"""

    @abstractmethod
    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """
        发送对话请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            AI 响应的文本内容
        """
        pass

    @abstractmethod
    async def generate_testcase(self, api_description: str, **kwargs) -> dict:
        """
        生成测试用例

        Args:
            api_description: API 描述文本
            **kwargs: 其他参数

        Returns:
            生成的测试用例配置
        """
        pass

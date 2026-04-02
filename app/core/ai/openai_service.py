import json
from typing import Optional

import httpx
from loguru import logger

from app.core.ai.base import AIService
from app.core.ai.prompt_template import PromptTemplate
from config import Config


class OpenAIService(AIService):
    """OpenAI 兼容 API 服务（支持 MiniMax 等）"""

    def __init__(self):
        self.api_key = Config.AI_OPENAI_API_KEY
        self.base_url = Config.AI_OPENAI_BASE_URL.rstrip("/")
        self.default_model = Config.AI_MODEL
        self.default_temperature = Config.AI_TEMPERATURE
        self.default_max_tokens = Config.AI_MAX_TOKENS
        self.prompt_template = PromptTemplate()

    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """
        发送对话请求到 AI 服务
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI API HTTP 错误: {e.response.text}")
            raise Exception(f"AI API 请求失败: {e.response.status_code}")
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI API 请求异常: {e}")
            raise

    async def generate_testcase(self, api_description: str, **kwargs) -> dict:
        """
        根据 API 描述生成测试用例

        Args:
            api_description: API 描述文本
            **kwargs: 可选参数

        Returns:
            测试用例配置字典
        """
        prompt = self.prompt_template.generate_case_prompt(api_description)
        messages = [{"role": "user", "content": prompt}]

        response = await self.chat(messages)
        return self._parse_testcase_response(response)

    async def enhance_asserts(self, case_info: dict, response_sample: str, **kwargs) -> list:
        """
        增强已有用例的断言

        Args:
            case_info: 用例信息
            response_sample: 响应示例
            **kwargs: 可选参数

        Returns:
            断言列表
        """
        prompt = self.prompt_template.enhance_asserts_prompt(case_info, response_sample)
        messages = [{"role": "user", "content": prompt}]

        response = await self.chat(messages)
        return self._parse_asserts_response(response)

    async def parse_curl(self, curl_command: str, **kwargs) -> dict:
        """
        解析 cURL 命令生成用例

        Args:
            curl_command: cURL 命令
            **kwargs: 可选参数

        Returns:
            测试用例配置
        """
        prompt = self.prompt_template.parse_curl_prompt(curl_command)
        messages = [{"role": "user", "content": prompt}]

        response = await self.chat(messages)
        return self._parse_testcase_response(response)

    async def batch_generate_from_openapi(self, openapi_spec: str, **kwargs) -> list:
        """
        从 OpenAPI 规范批量生成用例

        Args:
            openapi_spec: OpenAPI JSON/YAML 规范
            **kwargs: 可选参数

        Returns:
            用例配置列表
        """
        prompt = self.prompt_template.batch_generate_prompt(openapi_spec)
        messages = [{"role": "user", "content": prompt}]

        response = await self.chat(messages)
        return self._parse_batch_response(response)

    def _parse_testcase_response(self, response: str) -> dict:
        """
        解析 AI 生成的测试用例响应
        """
        try:
            # 尝试提取 JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError:
            logger.bind(name=Config.PITY_ERROR).warning(f"AI 响应 JSON 解析失败: {response[:200]}")
            raise Exception(f"AI 响应格式错误，无法解析为测试用例")

    def _parse_asserts_response(self, response: str) -> list:
        """
        解析 AI 生成的断言响应
        """
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            parsed = json.loads(response)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            logger.bind(name=Config.PITY_ERROR).warning(f"AI 断言响应 JSON 解析失败: {response[:200]}")
            raise Exception(f"AI 响应格式错误，无法解析为断言配置")

    def _parse_batch_response(self, response: str) -> list:
        """
        解析批量生成响应
        """
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            parsed = json.loads(response)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            logger.bind(name=Config.PITY_ERROR).warning(f"AI 批量生成响应 JSON 解析失败: {response[:200]}")
            raise Exception(f"AI 响应格式错误，无法解析为用例列表")


# 全局单例
ai_service = OpenAIService()

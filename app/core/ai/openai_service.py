import json
from typing import Optional, AsyncIterator

import httpx
from loguru import logger

from app.core.ai.base import AIService
from app.core.ai.prompt_template import PromptTemplate
from config import Config


class OpenAIService(AIService):
    """OpenAI 兼容 API 服务（支持 MiniMax、DeepSeek、GLM 等）"""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model_name: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        provider: str = "openai",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.default_model = model_name
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.provider = provider
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
        # 兼容不同 AI 服务商的 API 路径
        base = self.base_url.rstrip("/")
        if "minimaxi" in base:
            # MiniMax: 去掉 /anthropic，用 /v1/chat/completions
            base = base.replace("/anthropic", "").rstrip("/")
            url = f"{base}/v1/chat/completions"
        elif "bigmodel" in base:
            url = f"{base}/api/paas/v4/chat/completions"
        elif base.endswith("/v1") or base.endswith("/v1/"):
            # base_url 已经包含 /v1
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # 将 LangChain 消息对象转换为 dict 格式
        serialized_messages = []
        for msg in messages:
            if hasattr(msg, "to_dict"):
                serialized_messages.append(msg.to_dict())
            elif isinstance(msg, dict):
                serialized_messages.append(msg)
            else:
                # 兜底：假设是字符串或可直接序列化的对象
                serialized_messages.append({"role": "user", "content": str(msg)})

        payload = {
            "model": model or self.default_model,
            "messages": serialized_messages,
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
            error_detail = e.response.text
            status_code = e.response.status_code
            logger.bind(name=Config.PITY_ERROR).error(f"AI API HTTP 错误 [{status_code}]: {error_detail}")
            # 根据状态码给出友好提示
            if status_code == 401 or status_code == 403:
                raise Exception("AI API 认证失败，请检查 AI_OPENAI_API_KEY 是否正确")
            elif status_code == 404:
                raise Exception(f"AI API 地址错误，请检查 AI_OPENAI_BASE_URL 配置是否正确，当前: {url}")
            elif status_code == 422:
                raise Exception(f"AI 模型不存在或参数错误，请检查 AI_MODEL 配置是否正确，当前模型: {model or self.default_model}")
            elif status_code == 429:
                raise Exception("AI API 请求过于频繁，请稍后重试")
            elif status_code >= 500:
                raise Exception(f"AI 服务端错误 [{status_code}]，请稍后重试")
            else:
                raise Exception(f"AI API 请求失败 [{status_code}]: {error_detail[:200]}")
        except httpx.ConnectError as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI API 连接失败: {e}")
            raise Exception(f"AI API 连接失败，请检查 AI_OPENAI_BASE_URL 配置是否正确，当前: {url}")
        except httpx.TimeoutException:
            logger.bind(name=Config.PITY_ERROR).error("AI API 请求超时")
            raise Exception("AI API 请求超时，请检查网络连接或稍后重试")
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI API 请求异常: {e}")
            raise

    async def chat_stream(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        """
        发送对话请求到 AI 服务（流式响应）
        """
        base = self.base_url.rstrip("/")
        if "minimaxi" in base:
            base = base.replace("/anthropic", "").rstrip("/")
            url = f"{base}/v1/chat/completions"
        elif "bigmodel" in base:
            url = f"{base}/api/paas/v4/chat/completions"
        elif base.endswith("/v1") or base.endswith("/v1/"):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        serialized_messages = []
        for msg in messages:
            if hasattr(msg, "to_dict"):
                serialized_messages.append(msg.to_dict())
            elif isinstance(msg, dict):
                serialized_messages.append(msg)
            else:
                serialized_messages.append({"role": "user", "content": str(msg)})

        payload = {
            "model": model or self.default_model,
            "messages": serialized_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data)
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            status_code = e.response.status_code
            logger.bind(name=Config.PITY_ERROR).error(f"AI API HTTP 错误 [{status_code}]: {error_detail}")
            raise Exception(f"AI API 请求失败 [{status_code}]")
        except httpx.ConnectError as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI API 连接失败: {e}")
            raise Exception("AI API 连接失败")
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).error(f"AI API 流式响应异常: {e}")
            raise

    async def generate_testcase(self, api_description: str, **kwargs) -> dict:
        """
        根据 API 描述生成测试用例

        Args:
            api_description: API 描述文本
            **kwargs: 可选参数
                - rag_docs: RAG 检索到的相关文档字符串

        Returns:
            测试用例配置字典
        """
        rag_docs = kwargs.get("rag_docs", "")
        prompt = self.prompt_template.generate_case_prompt(api_description, rag_docs=rag_docs)
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
                - max_cases: 最大用例数量（默认 20）

        Returns:
            用例配置列表
        """
        import json

        max_cases = kwargs.get("max_cases", 20)

        # 尝试解析 OpenAPI 规范，提取路径列表
        try:
            spec = json.loads(openapi_spec)
            paths = spec.get("paths", {})
            path_list = list(paths.keys())

            # 如果路径太多，分批处理
            if len(path_list) > 10:
                return await self._batch_generate_by_paths(paths, max_cases)
        except json.JSONDecodeError:
            pass

        # 直接使用完整规范（路径较少时）
        prompt = self.prompt_template.batch_generate_prompt(openapi_spec, max_cases)
        messages = [{"role": "user", "content": prompt}]

        response = await self.chat(messages)
        return self._parse_batch_response(response)

    async def _batch_generate_by_paths(self, paths: dict, max_cases: int) -> list:
        """
        按路径分批生成用例

        Args:
            paths: OpenAPI paths 对象
            max_cases: 最大用例数量

        Returns:
            用例配置列表
        """
        import json

        all_cases = []
        path_list = list(paths.keys())[:max_cases]

        # 过滤出有实际业务意义的路径
        filtered_paths = {
            p: paths[p] for p in path_list
            if not any(k in p.lower() for k in ["health", "metrics", "ping", "swagger", "docs"])
        }

        if not filtered_paths:
            return []

        # 构造路径描述
        path_descs = []
        for path, methods in filtered_paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    summary = details.get("summary", details.get("description", ""))
                    path_descs.append(f"{method.upper()} {path}: {summary}")

        # 分批调用 AI
        batch_size = 5
        for i in range(0, len(path_descs), batch_size):
            batch = path_descs[i:i + batch_size]
            paths_str = "\n".join(batch)

            prompt = self.prompt_template.batch_generate_single_prompt(paths_str)
            messages = [{"role": "user", "content": prompt}]

            try:
                response = await self.chat(messages)
                cases = self._parse_batch_response(response)
                all_cases.extend(cases)

                # 达到上限则停止
                if len(all_cases) >= max_cases:
                    break
            except Exception as e:
                logger.bind(name=Config.PITY_ERROR).warning(f"批量生成批次 {i // batch_size + 1} 失败: {e}")
                continue

        return all_cases[:max_cases]

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

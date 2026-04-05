"""
OpenAPI 文档解析器
支持 Swagger 2.0 和 OpenAPI 3.0
"""
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import httpx
from loguru import logger

from config import Config


class OpenAPIParser:
    """OpenAPI 文档解析器"""

    def __init__(self):
        self.spec: Dict[str, Any] = {}
        self.api_version: str = ""
        self.base_url: str = ""
        self.title: str = ""

    async def parse_url(self, url: str) -> Dict[str, Any]:
        """
        从 URL 解析 OpenAPI 文档

        Args:
            url: OpenAPI JSON/YAML 文档 URL

        Returns:
            解析后的 API 定义列表
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                self.spec = response.json()
        except httpx.TimeoutException:
            raise Exception(f"请求 OpenAPI 文档超时: {url}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"请求 OpenAPI 文档失败 [{e.response.status_code}]: {url}")
        except json.JSONDecodeError:
            raise Exception("OpenAPI 文档不是有效的 JSON 格式")

        return self._parse()

    def parse_content(self, content: str) -> Dict[str, Any]:
        """
        从文件内容解析 OpenAPI 文档

        Args:
            content: OpenAPI JSON/YAML 文档内容

        Returns:
            解析后的 API 定义列表
        """
        try:
            self.spec = json.loads(content)
        except json.JSONDecodeError:
            raise Exception("OpenAPI 文档不是有效的 JSON 格式")

        return self._parse()

    def _parse(self) -> Dict[str, Any]:
        """解析 OpenAPI 文档"""
        if not self.spec:
            raise Exception("OpenAPI 文档为空")

        # 判断版本
        if "swagger" in self.spec:
            self.api_version = "2.0"
        elif "openapi" in self.spec:
            self.api_version = "3.0"
        else:
            raise Exception("不支持的 OpenAPI 格式，请确认文档为 Swagger 2.0 或 OpenAPI 3.0")

        # 提取基本信息
        self.title = self.spec.get("info", {}).get("title", "API")
        self.base_url = self._get_base_url()

        # 解析 API 列表
        apis = self._parse_paths()

        return {
            "title": self.title,
            "version": self.api_version,
            "base_url": self.base_url,
            "apis": apis,
            "total": len(apis)
        }

    def _get_base_url(self) -> str:
        """获取基础 URL"""
        if self.api_version == "2.0":
            base_path = self.spec.get("basePath", "")
            schemes = self.spec.get("schemes", ["https"])
            host = self.spec.get("host", "")
            return f"{schemes[0]}://{host}{base_path}"
        else:  # OpenAPI 3.0
            servers = self.spec.get("servers", [])
            if servers:
                return servers[0].get("url", "")
            return ""

    def _parse_paths(self) -> List[Dict[str, Any]]:
        """解析所有路径"""
        paths = self.spec.get("paths", {})
        apis = []

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
                    continue

                api = self._parse_api(path, method, details)
                if api:
                    apis.append(api)

        return apis

    def _parse_api(self, path: str, method: str, details: Dict) -> Optional[Dict[str, Any]]:
        """解析单个 API"""
        if details.get("deprecated"):
            return None

        # 获取标签
        tags = details.get("tags", ["默认"])

        # 获取摘要/描述
        summary = details.get("summary", details.get("description", ""))
        description = details.get("description", "")

        # 解析参数
        params = self._parse_parameters(details)

        # 解析请求体（OpenAPI 3.0）
        request_body = self._parse_request_body(details)

        # 解析响应
        responses = self._parse_responses(details)

        return {
            "path": path,
            "method": method.upper(),
            "summary": summary,
            "description": description,
            "tags": tags,
            "parameters": params,
            "request_body": request_body,
            "responses": responses,
        }

    def _parse_parameters(self, details: Dict) -> Dict[str, List[Dict]]:
        """解析参数（path/query/header）"""
        params = {"path": [], "query": [], "header": []}

        for param in details.get("parameters", []):
            p = {
                "name": param.get("name", ""),
                "type": param.get("type", "string"),
                "required": param.get("required", False),
                "description": param.get("description", ""),
                "default": param.get("default"),
                "enum": param.get("enum"),
            }

            location = param.get("in", "query")
            if location in params:
                params[location].append(p)

        return params

    def _parse_request_body(self, details: Dict) -> Optional[Dict]:
        """解析请求体（OpenAPI 3.0）"""
        if self.api_version != "3.0":
            return None

        request_body = details.get("requestBody")
        if not request_body:
            return None

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        return {
            "description": request_body.get("description", ""),
            "required": request_body.get("required", False),
            "schema": self._parse_schema(schema),
        }

    def _parse_schema(self, schema: Dict) -> Dict:
        """解析 JSON Schema"""
        if not schema:
            return {}

        result = {
            "type": schema.get("type", "object"),
            "description": schema.get("description", ""),
        }

        # 处理对象类型
        if schema.get("type") == "object" or schema.get("properties"):
            properties = {}
            for name, prop in schema.get("properties", {}).items():
                properties[name] = self._parse_schema(prop)
            result["properties"] = properties

        # 处理数组类型
        if schema.get("type") == "array" or schema.get("items"):
            result["items"] = self._parse_schema(schema.get("items", {}))

        # 处理枚举
        if schema.get("enum"):
            result["enum"] = schema["enum"]

        # 处理引用
        if schema.get("$ref"):
            result["ref"] = schema["$ref"].split("/")[-1]

        return result

    def _parse_responses(self, details: Dict) -> Dict[str, Dict]:
        """解析响应"""
        responses = {}

        for code, resp in details.get("responses", {}).items():
            content = resp.get("content", {})
            json_resp = content.get("application/json", {})
            schema = json_resp.get("schema", {})

            responses[code] = {
                "description": resp.get("description", ""),
                "schema": self._parse_schema(schema),
            }

        return responses


# 全局单例
openapi_parser = OpenAPIParser()

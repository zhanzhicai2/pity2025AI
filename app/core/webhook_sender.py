"""
Webhook 发送服务
"""
import hashlib
import hmac
import time
import httpx
import json
from loguru import logger

from config import Config


class WebhookSender:
    """Webhook 发送器"""

    @staticmethod
    def generate_dingtalk_sign(secret: str) -> str:
        """生成钉钉加签"""
        timestamp = str(int(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        sign = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).base64().decode("utf-8")
        return timestamp, sign

    @staticmethod
    def generate_wework_sign(token: str) -> str:
        """生成企业微信加签"""
        timestamp = str(int(time.time()))
        string_to_sign = f"GET&".join([
            "",
            "",
            timestamp,
            hashlib.sha256(token.encode("utf-8")).hexdigest()
        ])
        sign = hashlib.sha256(string_to_sign.encode("utf-8")).hexdigest()
        return timestamp, sign

    @classmethod
    async def send(
        cls,
        url: str,
        method: str = "POST",
        headers: dict = None,
        body: dict = None,
        secret: str = None,
        content_type: str = "json"
    ) -> dict:
        """
        发送 HTTP 请求

        Args:
            url: 目标 URL
            method: 请求方法
            headers: 请求头
            body: 请求体
            secret: 签名密钥（用于钉钉/企业微信）
            content_type: Content-Type

        Returns:
            {"success": True, "status_code": 200, "response": "..."}
            或 {"success": False, "error": "..."}
        """
        headers = headers or {}

        # 如果有 secret，尝试添加签名（钉钉格式）
        if secret:
            # 钉钉加签格式
            timestamp, sign = cls.generate_dingtalk_sign(secret)
            if "?" in url:
                url += f"&timestamp={timestamp}&sign={sign}"
            else:
                url += f"?timestamp={timestamp}&sign={sign}"

        # 设置 Content-Type
        if content_type == "json":
            headers["Content-Type"] = headers.get("Content-Type", "application/json")
        elif content_type == "text":
            headers["Content-Type"] = headers.get("Content-Type", "text/plain")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=body)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=body)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return {"success": False, "error": f"不支持的请求方法: {method}"}

                response.raise_for_status()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.text[:500]  # 截断响应
                }

        except httpx.TimeoutException:
            logger.bind(name=Config.PITY_ERROR).error(f"Webhook 请求超时: {url}")
            return {"success": False, "error": "请求超时"}
        except httpx.HTTPStatusError as e:
            logger.bind(name=Config.PITY_ERROR).error(f"Webhook HTTP 错误: {e}")
            return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.bind(name=Config.PITY_ERROR).error(f"Webhook 发送异常: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def send_test(
        cls,
        url: str,
        method: str = "POST",
        headers: str = None,
        body: str = None,
        secret: str = None,
        content_type: str = "json"
    ) -> dict:
        """发送测试请求"""
        # 解析 headers
        headers_dict = {}
        if headers:
            try:
                headers_dict = json.loads(headers)
            except json.JSONDecodeError:
                return {"success": False, "error": "headers 格式错误，请输入有效的 JSON"}

        # 解析 body
        body_dict = None
        if body:
            try:
                body_dict = json.loads(body)
            except json.JSONDecodeError:
                return {"success": False, "error": "body 格式错误，请输入有效的 JSON"}

        return await cls.send(url, method, headers_dict, body_dict, secret, content_type)

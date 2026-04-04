"""
Redis 缓存服务
"""
import hashlib
import json
from typing import Optional

from config import Config
from redis import Redis


class CacheService:
    """Redis 缓存服务"""

    def __init__(self):
        self.client = Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
            decode_responses=True
        )

    @staticmethod
    def _make_key(prefix: str, text: str) -> str:
        hash_key = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"rag:{prefix}:{hash_key}"

    def get(self, prefix: str, text: str) -> Optional[dict]:
        """获取缓存"""
        key = self._make_key(prefix, text)
        cached = self.client.get(key)
        if cached:
            return json.loads(cached)
        return None

    def set(self, prefix: str, text: str, data: dict, ttl: int = 3600):
        """设置缓存"""
        key = self._make_key(prefix, text)
        self.client.setex(key, ttl, json.dumps(data, ensure_ascii=False))

    def invalidate(self, prefix: str, text: str):
        """删除缓存"""
        key = self._make_key(prefix, text)
        self.client.delete(key)

    def invalidate_prefix(self, prefix: str):
        """删除指定前缀的所有缓存"""
        pattern = f"rag:{prefix}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

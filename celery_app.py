"""
Celery 异步任务配置

使用方式:
1. 启动 Worker: celery -A celery_app worker --loglevel=info
2. 启动 Beat (可选): celery -A celery_app beat --loglevel=info
3. 启动 Flower: celery -A celery_app flower --port=5555
"""
from celery import Celery

from config import Config

# 构建 Redis 连接 URL
redis_host = Config.REDIS_HOST or 'localhost'
redis_port = Config.REDIS_PORT or 6379
redis_db = Config.REDIS_DB or 0
redis_password = Config.REDIS_PASSWORD

if redis_password:
    broker_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
else:
    broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

# 创建 Celery 应用
celery_app = Celery(
    'pity',
    broker=broker_url,
    backend=broker_url,
    include=['app.tasks.ai_tasks']
)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 任务最大执行时间 5 分钟
    task_soft_time_limit=240,  # 软限制 4 分钟
    worker_prefetch_multiplier=1,  # 防止任务积压
    task_acks_late=True,  # 任务完成后确认
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 结果过期时间 1 小时
)

# 自动发现任务
celery_app.autodiscover_tasks(['app.tasks'])

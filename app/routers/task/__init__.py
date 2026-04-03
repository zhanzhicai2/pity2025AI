"""
任务路由
"""
from app.routers.task.celery_router import router as celery_router

__all__ = ['celery_router']

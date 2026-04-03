"""
Celery 异步任务包
"""
from app.tasks.ai_tasks import generate_testcase, enhance_asserts

__all__ = ['generate_testcase', 'enhance_asserts']

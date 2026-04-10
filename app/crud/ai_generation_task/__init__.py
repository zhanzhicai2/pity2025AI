from app.crud import Mapper, ModelWrapper
from app.models.ai_generation_task import PityAIGenerationTask


@ModelWrapper(PityAIGenerationTask)
class AIGenerationTaskDao(Mapper):
    """AI 生成任务 DAO"""
    pass

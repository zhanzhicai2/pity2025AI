"""
Phase X DAO
"""
from app.crud import Mapper, ModelWrapper
from app.models.phasex import PityPhaseXPlan, PityPhaseXExecution, PityPhaseXReport


@ModelWrapper(PityPhaseXPlan)
class PityPhaseXPlanDao(Mapper):
    """Phase X 测试计划 DAO"""
    pass


@ModelWrapper(PityPhaseXExecution)
class PityPhaseXExecutionDao(Mapper):
    """Phase X 执行记录 DAO"""
    pass


@ModelWrapper(PityPhaseXReport)
class PityPhaseXReportDao(Mapper):
    """Phase X 测试报告 DAO"""
    pass

"""
场景流程 DAO
"""
from app.crud import Mapper, ModelWrapper
from app.models.scenario import PityScenario, PityScenarioStep


@ModelWrapper(PityScenario)
class PityScenarioDao(Mapper):
    """场景流程 DAO"""
    pass


@ModelWrapper(PityScenarioStep)
class PityScenarioStepDao(Mapper):
    """场景步骤 DAO"""
    pass

from app.crud import Mapper, ModelWrapper
from app.models.case_v2 import PityCaseV2


@ModelWrapper(PityCaseV2)
class CaseV2Dao(Mapper):
    """用例主表 DAO"""
    pass

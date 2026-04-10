from app.crud import Mapper, ModelWrapper
from app.models.testcase_template import PityTestcaseTemplate


@ModelWrapper(PityTestcaseTemplate)
class TestcaseTemplateDao(Mapper):
    """模板 DAO"""
    pass
